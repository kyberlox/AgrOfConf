# app/requests/router/requests.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.contact_person import ContactPerson
from ..schema.contact_person import ContactResponse
from ..model.customer import Customer
from ..model.database import get_db
from ..model.request import Request
from ..schema.request import RequestCreate, RequestCreateResponse, RequestResponse, RequestUpdate
from ..schema.customer import CustomerResponse
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


@router.post(
    "/",
    response_model=RequestCreateResponse,
    status_code=201,
)
async def create_request(
        payload: RequestCreate,
        user_id: int = Depends(get_active_user_id),
        db: AsyncSession = Depends(get_db),
):
    try:
        # 1. Получаем существующего либо создаём нового заказчика
        if payload.customer_id is not None:
            customer_result = await db.execute(
                select(Customer).where(
                    Customer.id == payload.customer_id
                )
            )
            customer = customer_result.scalar_one_or_none()

            if customer is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Заказчик с id={payload.customer_id} не найден"
                    ),
                )
        else:
            if payload.customer is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Если customer_id не передан, "
                        "необходимо передать customer"
                    ),
                )

            customer = Customer(
                **payload.customer.model_dump(exclude_none=True)
            )

            db.add(customer)
            await db.flush()

        # 2. Получаем существующую либо создаём новую организацию
        if payload.organization_id is not None:
            organization_result = await db.execute(
                select(Customer).where(
                    Customer.id == payload.organization_id
                )
            )
            organization = organization_result.scalar_one_or_none()

            if organization is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Организация с id={payload.organization_id} не найдена"
                    ),
                )

        else:
            if payload.organization is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        "Если organization_id не передан, "
                        "необходимо передать organization"
                    ),
                )

            organization = Customer(
                **payload.organization.model_dump(exclude_none=True)
            )

            db.add(organization)
            await db.flush()

        # 3. Создаём запрос
        db_request = Request(
            user_id=user_id,
            customer_id=customer.id,
            organization_id=organization.id,
            request_purpose=payload.request_purpose,
            description=payload.description,
            construction_project=payload.construction_project,
            tkp_term=payload.tkp_term,
            delivery_time=payload.delivery_time,
            procedure_type=payload.procedure_type,
        )

        db.add(db_request)
        await db.flush()

        # 4. Создаём контакты заказчика
        created_contacts: list[ContactPerson] = []

        for contact_data in payload.contacts:
            contact = ContactPerson(
                **contact_data.model_dump(exclude_none=True),
                customer_id=customer.id,
            )

            db.add(contact)
            created_contacts.append(contact)

        if created_contacts:
            await db.flush()

        await db.refresh(customer)
        await db.refresh(organization)
        await db.refresh(db_request)

        for contact in created_contacts:
            await db.refresh(contact)

        response = RequestCreateResponse(
            id=db_request.id,
            customer_id=db_request.customer_id,
            organization_id=db_request.organization_id,
            request_purpose=db_request.request_purpose,
            description=db_request.description,
            construction_project=db_request.construction_project,
            tkp_term=db_request.tkp_term,
            delivery_time=db_request.delivery_time,
            procedure_type=db_request.procedure_type,
            customer=customer,
            contacts=created_contacts,
        )

        await db.commit()

        return response

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
            detail="Не удалось создать запрос из-за конфликта данных",
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Запрос с id={request_id} не найден",
            )

        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не передано ни одного поля для изменения",
            )

        # Если меняется заказчик, проверяем его наличие
        if "customer_id" in update_data:
            customer_id = update_data["customer_id"]

            if customer_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="customer_id не может быть null",
                )

            customer_result = await db.execute(
                select(Customer.id).where(
                    Customer.id == customer_id
                )
            )
            customer_exists = customer_result.scalar_one_or_none()

            if customer_exists is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Заказчик с id={customer_id} не найден",
                )

        # Если меняется организация, проверяем её наличие
        if (
                "organization_id" in update_data
                and update_data["organization_id"] is not None
        ):
            organization_id = update_data["organization_id"]

            organization_result = await db.execute(
                select(Customer.id).where(
                    Customer.id == organization_id
                )
            )
            organization_exists = (
                organization_result.scalar_one_or_none()
            )

            if organization_exists is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Организация с id={organization_id} "
                        "не найдена"
                    ),
                )

        for field_name, field_value in update_data.items():
            setattr(db_request, field_name, field_value)

        await db.flush()
        await db.refresh(db_request)

        response = RequestResponse.model_validate(db_request)
        await db.commit()
        return response

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Не удалось изменить запрос из-за конфликта данных",
        ) from exc

    except Exception as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        current_user_id: int = Depends(get_active_user_id),
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
        db: AsyncSession = Depends(get_db),
):
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к запросам другого пользователя",
        )

    result = await db.execute(
        select(Request)
        .where(Request.user_id == user_id)
        .order_by(Request.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return result.scalars().all()
