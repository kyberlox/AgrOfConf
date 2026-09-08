import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/homeView/HomeView.vue';
import Api from '@/utils/Api';
import { useUserStore } from '@/stores/user';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  linkActiveClass: 'router-link-active',
  routes: [
    {
      path: '/login',
      name: 'login',
      beforeEnter: (to, from, next) => {
        window.open('https://intranet.emk.ru/api/auth_router/argconf');
        next(false)
      },
      redirect: '',
    },
    {
      path: '/',
      name: 'homeview',
      redirect: '/my_requests',
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/admin/ProductsList.vue/ProductList.vue')
    },
    {
      path: '/admin/product/:id',
      name: 'productEdit',
      component: () => import('../views/admin/product/Product.vue'),
      props: (route) => ({ id: route.params.id })
    },
    {
      path: '/configurator/:id',
      name: 'configurator',
      component: () => import('../views/configurator/Configurator.vue'),
      props: (route) => ({ id: route.params.id })
    },
    {
      path: '/user/:id',
      name: 'user',
      component: () => import('../views/userPage/UserPage.vue'),
      props: (route) => ({ id: route.params.id })
    },
    {
      path: '/my_requests',
      name: 'myRequests',
      component: HomeView,
    },
    {
      path: '/ko_requests',
      name: 'koRequests',
      component: HomeView,
    },

  ]
})

router.beforeEach(async (to) => {
    const adminRoutes = ['admin', 'productEdit']
    if (adminRoutes.includes(String(to.name))) {
        const userStore = useUserStore()
        let isAdmin = userStore.getIsAdmin
        if (!isAdmin) {
            const userId = await Api.get('auth/user_id_by_session_id')
            if (userId) {
                isAdmin = Boolean(await Api.get(`roots/access_admin?user_id=${userId}`))
                userStore.setIsAdmin(isAdmin)
            }
        }
        if (!isAdmin) return { name: 'myRequests' }
    }
    return true
})

export default router
