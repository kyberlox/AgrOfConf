import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/homeView/HomeView.vue';

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

export default router
