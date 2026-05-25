import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
   linkActiveClass: 'router-link-active',
  routes: [
    {
      path: '/',
      name: 'homeview',
      props: ()=> ({ type: 'requests' }),
      component: () => import('../views/homeView/HomeView.vue')
    },
    {
      path: '/statistics/user',
      name: 'userStatistics',
      props: ()=> ({ type: 'statistics' }),
      component: () => import('../views/homeView/HomeView.vue')
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
      props: (route)=> ({ id: route.params.id })
    },
    {
      path: '/configurator/:id',
      name: 'configurator',
      component: () => import('../views/configurator/Configurator.vue'),
      props: (route)=> ({ id: route.params.id })
    }
  ]
  })

export default router
