# app/requests/router/requests.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..model.contact_person import ContactPerson
from ..schema.contact_person import ContactResponse
from ..model.customer import Customer
from ..model.database import get_db
from ..model.request import Request
from ..schema.request import RequestCreate, RequestResponse, RequestUpdate, RequestData
from ..schema.customer import CustomerRequest, CustomerResponse
from ...UserService.model.Users import Users
from ...UserService.utils.auth_utils import get_user_id_by_session_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/requests",
    tags=["Requests"],
)


async def get_active_user_id(
        user_id: int = Depends(get_user_id_by_session_id),
        db: AsyncSession = Depends(get_db),
) -> int:
    result = await db.execute(
        select(Users.id, Users.is_active).where(Users.id == user_id)
    )
    user = result.one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь сессии не найден",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован",
        )

    return user.id


async def get_request_with_relations(
        request_id: int,
        db: AsyncSession,
        user_id: int | None = None,
):
    statement = (
        select(Request)
        .options(
            selectinload(Request.customer)
            .selectinload(Customer.contacts),

            selectinload(Request.organization)
            .selectinload(Customer.contacts),

            selectinload(Request.end_customer)
            .selectinload(Customer.contacts),
        )
        .where(Request.id == request_id)
    )

    if user_id is not None:
        statement = statement.where(Request.user_id == user_id)

    result = await db.execute(statement)

    db_request = result.scalar_one_or_none()

    if db_request is None:
        raise HTTPException(
            status_code=404,
            detail=f"Запрос с id={request_id} не найден",
        )

    return RequestResponse(
        id=db_request.id,
        request_num=db_request.request_num,
        status=db_request.status,

        request=RequestData(
            request_purpose=db_request.request_purpose,
            description=db_request.description,
            construction_project=db_request.construction_project,
            tkp_term=db_request.tkp_term,
            delivery_time=db_request.delivery_time,
            procedure_type=db_request.procedure_type,
        ),

        customer=db_request.customer,
        organization=db_request.organization,
        end_customer=db_request.end_customer,
    )


async def get_or_create_customer(
        data: CustomerRequest,
        role_name: str,
        db: AsyncSession,
):
    # Если передан ID — берём существующего
    if data.id is not None:
        result = await db.execute(
            select(Customer)
            .where(Customer.id == data.id)
        )

        customer = result.scalar_one_or_none()

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"{role_name} с id={data.id} не найден"
                ),
            )

        return customer

    # Если ID нет — создаём нового
    if not data.organization:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Для нового объекта '{role_name}' "
                "необходимо указать organization"
            ),
        )

    customer_data = data.model_dump(
        exclude={"id", "contacts"},
        exclude_none=True,
    )

    customer = Customer(**customer_data)

    db.add(customer)

    await db.flush()

    # Создаём контакты этого объекта
    for contact_data in data.contacts:
        contact = ContactPerson(
            **contact_data.model_dump(exclude_none=True),
            customer_id=customer.id,
        )

        db.add(contact)

    return customer


@router.post(
    "/",
    response_model=RequestResponse,
    status_code=201,
)
async def create_request(
        payload: RequestCreate,
        user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Клиент / заказчик
        customer = await get_or_create_customer(
            data=payload.customer,
            role_name="Заказчик",
            db=db,
        )

        # 2. Проектная организация
        organization = await get_or_create_customer(
            data=payload.organization,
            role_name="Проектная организация",
            db=db,
        )

        # 3. Конечный заказчик
        end_customer = None

        if payload.end_customer is not None:
            end_customer = await get_or_create_customer(
                data=payload.end_customer,
                role_name="Конечный заказчик",
                db=db,
            )

        # 4. Создаём сам запрос
        db_request = Request(
            user_id=user_id,

            customer_id=customer.id,
            organization_id=organization.id,
            end_customer_id=(
                end_customer.id
                if end_customer is not None
                else None
            ),

            request_purpose=payload.request.request_purpose,
            description=payload.request.description,
            construction_project=(
                payload.request.construction_project
            ),
            tkp_term=payload.request.tkp_term,
            delivery_time=payload.request.delivery_time,
            procedure_type=payload.request.procedure_type,
        )

        db.add(db_request)

        await db.flush()

        await db.commit()

        return await get_request_with_relations(
            db_request.id,
            db,
            user_id,
        )

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError as exc:
        await db.rollback()

        logger.exception(
            "Ошибка целостности при создании запроса"
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Не удалось создать запрос "
                "из-за конфликта данных"
            ),
        ) from exc

    except Exception as exc:
        await db.rollback()

        logger.exception(
            "Ошибка создания запроса: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании запроса",
        ) from exc


@router.get(
    "/customers/search",
    response_model=list[CustomerResponse],
    description="Поиск заказчиков по названию организации.",
)
async def search_customers(
        query: str = Query(
            ...,
            min_length=1,
            max_length=200,
            description="Название организации или его часть",
        ),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        _user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    normalized_query = query.strip()

    if not normalized_query:
        return []

    lowered_query = normalized_query.lower()

    search_priority = case(
        (
            func.lower(Customer.organization) == lowered_query,
            0,
        ),
        (
            func.lower(Customer.organization).like(
                f"{lowered_query}%"
            ),
            1,
        ),
        else_=2,
    )

    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.contacts))
        .where(
            Customer.organization.is_not(None),
            Customer.organization.ilike(
                f"%{normalized_query}%"
            ),
            Customer.visibility.is_(True),
        )
        .order_by(
            search_priority,
            Customer.organization.asc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return result.scalars().all()


@router.get(
    "/contacts/search",
    response_model=list[ContactResponse],
    description="Поиск контактных лиц по ФИО.",
)
async def search_contacts(
        query: str = Query(
            ...,
            min_length=1,
            max_length=200,
            description="ФИО контактного лица или его часть",
        ),
        customer_id: int | None = Query(
            default=None,
            ge=1,
            description="Ограничить поиск контактами конкретного заказчика",
        ),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
        _user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    normalized_query = query.strip()

    if not normalized_query:
        return []

    lowered_query = normalized_query.lower()

    search_priority = case(
        (
            func.lower(ContactPerson.full_name) == lowered_query,
            0,
        ),
        (
            func.lower(ContactPerson.full_name).like(
                f"{lowered_query}%"
            ),
            1,
        ),
        else_=2,
    )

    statement = (
        select(ContactPerson)
        .where(
            ContactPerson.full_name.ilike(
                f"%{normalized_query}%"
            ),
            ContactPerson.visibility.is_(True),
        )
    )

    if customer_id is not None:
        statement = statement.where(
            ContactPerson.customer_id == customer_id
        )

    statement = (
        statement
        .order_by(
            search_priority,
            ContactPerson.full_name.asc(),
        )
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(statement)

    return result.scalars().all()


@router.patch(
    "/{request_id}",
    response_model=RequestResponse,
    description="Частичное изменение запроса по его ID.",
)
async def update_request(
        request_id: int,
        payload: RequestUpdate,
        user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(Request).where(
                Request.id == request_id,
                Request.user_id == user_id,
            )
        )

        db_request = result.scalar_one_or_none()

        if db_request is None:
            raise HTTPException(
                status_code=404,
                detail=f"Запрос с id={request_id} не найден",
            )

        # -------------------------
        # 1. Изменение данных request
        # -------------------------

        if payload.request is not None:
            request_data = payload.request.model_dump(
                exclude_unset=True
            )

            for field_name, field_value in request_data.items():
                setattr(
                    db_request,
                    field_name,
                    field_value
                )

        if payload.customer is not None:
            customer = await get_or_create_customer(
                payload.customer,
                "Заказчик",
                db,
            )
            db_request.customer_id = customer.id

        if payload.organization is not None:
            organization = await get_or_create_customer(
                payload.organization,
                "Проектная организация",
                db,
            )
            db_request.organization_id = organization.id

        if payload.end_customer is not None:
            end_customer = await get_or_create_customer(
                payload.end_customer,
                "Конечный заказчик",
                db,
            )
            db_request.end_customer_id = end_customer.id

        await db.commit()

        return await get_request_with_relations(
            request_id,
            db,
            user_id,
        )

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Не удалось изменить запрос",
        ) from exc

    except Exception as exc:
        await db.rollback()

        logger.exception(
            "Ошибка изменения запроса: %s",
            exc
        )

        raise HTTPException(
            status_code=500,
            detail="Ошибка при изменении запроса",
        ) from exc


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK,
    description="Удаление запроса по его ID.",
)
async def delete_request(
        request_id: int,
        user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Request).where(
            Request.id == request_id,
            Request.user_id == user_id,
        )
    )
    db_request = result.scalar_one_or_none()

    if db_request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запрос с id={request_id} не найден",
        )

    await db.delete(db_request)
    await db.commit()

    return {
        "detail": "Запрос успешно удалён",
        "request_id": request_id,
    }


@router.get(
    "/users/{user_id}",
    response_model=list[RequestResponse],
    description="Выведение всех запросов пользователя.",
)
async def get_user_requests(
        user_id: int,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Request)
        .options(
            selectinload(Request.customer)
            .selectinload(Customer.contacts),

            selectinload(Request.organization)
            .selectinload(Customer.contacts),

            selectinload(Request.end_customer)
            .selectinload(Customer.contacts),
        )
        .where(
            Request.user_id == user_id
        )
        .order_by(
            Request.id.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    requests = result.scalars().all()

    return [
        RequestResponse(
            id=request.id,
            request_num=request.request_num,
            status=request.status,

            request=RequestData(
                request_purpose=request.request_purpose,
                description=request.description,
                construction_project=request.construction_project,
                tkp_term=request.tkp_term,
                delivery_time=request.delivery_time,
                procedure_type=request.procedure_type,
            ),

            customer=request.customer,
            organization=request.organization,
            end_customer=request.end_customer,
        )
        for request in requests
    ]


@router.get(
    "/{request_id}",
    response_model=RequestResponse,
    description="Получение запроса по ID.",
)
async def get_request(
        request_id: int,
        user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    return await get_request_with_relations(
        request_id,
        db,
        user_id,
    )
