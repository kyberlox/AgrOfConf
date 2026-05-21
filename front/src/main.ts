import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import DropZone from 'dropzone-vue';

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(DropZone)

app.mount('#app')
