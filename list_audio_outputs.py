import win32com.client

voice = win32com.client.Dispatch("SAPI.SpVoice")
outputs = voice.GetAudioOutputs()

for i in range(outputs.Count):
    print(f"{i}: {outputs.Item(i).GetDescription()}")
