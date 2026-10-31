import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './presentation/router'
import clickOutside from './presentation/directives/clickOutside'

const app = createApp(App)
app.directive('click-outside', clickOutside)
app.use(router)
app.mount('#app')
