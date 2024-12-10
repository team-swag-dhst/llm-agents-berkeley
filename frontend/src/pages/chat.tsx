import ChatBot, { Button } from "react-chatbotify";

export const Chat = () => {
  const flow = {
    start: {
      message: "Hey! Look at my messages stream in, pretty cool isn't it?",
      path: "thank",
    },
    thank: {
      message: async (params: any) => {
        await params.injectMessage("I am an injected message!");
        return "I am a return message!";
      },
      path: "start",
    },
  };
  const styles = {
    headerStyle: {
      background: "#42b0c5",
      color: "#ffffff",
      padding: "10px",
    },
    chatWindowStyle: {
      width: "100%",
      height: "90vh",
    },
    // ...other styles
  };
  // const themes = [{ id: "omen", version: "0.1.0" }];
  const settings = {
    general: { embedded: true },
    chatHistory: { storageKey: "example_simulation_stream" },
    botBubble: { simStream: true },
    header: {
		title: (
			<div 
            // style={{cursor: "pointer", margin: 0, fontSize: 20, fontWeight: "bold"}} onClick={
			// 	() => window.open("https://github.com/tjtanjin/")
			// }
            >
				Team Swag
			</div>
		),
		showAvatar: true,
		// avatar: botAvatar,
		buttons: [Button.NOTIFICATION_BUTTON, Button.AUDIO_BUTTON, Button.CLOSE_CHAT_BUTTON],
		// closeChatIcon: CloseChatIcon,
	},
  };

  return (
    <div style={{ padding: "2rem" }}>
      <ChatBot
        settings={settings}
        // themes={themes}
        styles={styles}
        flow={flow}
      />
    </div>
  );
};
