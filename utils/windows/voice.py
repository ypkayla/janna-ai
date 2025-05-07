import time
import os
import win32com.client
import utils.hotkeys
import utils.voice_splitter
import utils.zw_logging
import utils.soundboard
import utils.settings
import API.api_controller

is_speaking = False
cut_voice = False

def speak_line(s_message, refuse_pause):

    global cut_voice #, is_speaking
    cut_voice = False

    chunky_message = utils.voice_splitter.split_into_sentences(s_message)

    # Verbinde die SAPI SpVoice und wähle die Audio-Ausgabe
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    outputs = speaker.GetAudioOutputs()

    # Durchsuchen der Ausgabegeräte und Suche nach "VB-Cable"
    vb_cable_index = None
    for i in range(outputs.Count):
        if "VB-Cable" in outputs.Item(i).GetDescription():
            vb_cable_index = i
            break

    if vb_cable_index is not None:
        speaker.AudioOutput = outputs.Item(vb_cable_index)  # Setze VB-Cable als Ausgabegerät
    else:
        # Wenn VB-Cable nicht gefunden wird, gibt es eine Fehlermeldung
        utils.zw_logging.update_debug_log("VB-Cable nicht gefunden, standardmäßiges Ausgabegerät wird verwendet.")
    
    for chunk in chunky_message:
        try:
            # Play soundboard sounds, if any
            pure_chunk = utils.soundboard.extract_soundboard(chunk)

            # Cut out if we are not speaking unless spoken to!
            if utils.settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                continue

            # Speak
            speaker.Speak(pure_chunk)

            if not refuse_pause:
                time.sleep(0.05)    # IMPORTANT: Mini-rests between chunks for other calculations in the program to run.
            else:
                time.sleep(0.001)   # Still have a mini-mini rest, even with pauses

            # Break free if we undo/redo, and stop reading
            if utils.hotkeys.NEXT_PRESSED or utils.hotkeys.REDO_PRESSED or cut_voice:
                cut_voice = False
                break

        except:
            utils.zw_logging.update_debug_log("Error with voice!")

    # Reset the volume cooldown so she don't pickup on herself
    utils.hotkeys.cooldown_listener_timer()

    set_speaking(False)

    return

# Midspeaking (still processing whole message)
def check_if_speaking() -> bool:
    return is_speaking

def set_speaking(set: bool):
    global is_speaking
    is_speaking = set

def force_cut_voice():
    global cut_voice
    cut_voice = True
