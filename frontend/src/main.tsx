import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
async function enableMocking(){
  if(!import.meta.env.DEV){
    return ;
  }
  return Promise.resolve().then(()=>import("./mock/mock").then(({worker}:any)=>{
    return worker.start()
  }))
}
enableMocking().then(()=>{
  if(import.meta.env.DEV){
    createRoot(document.getElementById('root')!).render(
        <App />
    )
  }else{
    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  }
})
