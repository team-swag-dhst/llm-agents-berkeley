import { ChatBotProvider } from 'react-chatbotify'
import './App.css'
import { Chat } from './pages/chat'

function App() {

  return (
    <>
    <ChatBotProvider>

    <Chat/>
    </ChatBotProvider>
    </>
  )
}

export default App
