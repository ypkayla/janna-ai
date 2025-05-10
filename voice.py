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
    global cut_voice
    cut_voice = False

    chunky_message = utils.voice_splitter.split_into_sentences(s_message)

    # Verbinde die SAPI SpVoice und hole die Audio-Ausgänge
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    outputs = speaker.GetAudioOutputs()

    # Suche nach "VB-Cable" Ausgabegerät
    vb_cable_index = None
    for i in range(outputs.Count):
        if "VB-Cable" in outputs.Item(i).GetDescription():
            vb_cable_index = i
            break

    if vb_cable_index is not None:
        speaker.AudioOutput = outputs.Item(vb_cable_index)
        utils.zw_logging.update_debug_log(f"VB-Cable gefunden und gesetzt (Index {vb_cable_index})")
    else:
        utils.zw_logging.update_debug_log("VB-Cable nicht gefunden, Standardgerät wird verwendet.")

    for chunk in chunky_message:
        try:
            pure_chunk = utils.soundboard.extract_soundboard(chunk)

            if utils.settings.speak_only_spokento and not API.api_controller.last_message_received_has_own_name:
                continue

            speaker.Speak(pure_chunk)

            if not refuse_pause:
                time.sleep(0.05)
            else:
                time.sleep(0.001)

            if utils.hotkeys.NEXT_PRESSED or utils.hotkeys.REDO_PRESSED or cut_voice:
                cut_voice = False
                break

        except Exception as e:
            utils.zw_logging.update_debug_log(f"Error with voice: {e}")

    utils.hotkeys.cooldown_listener_timer()
    set_speaking(False)
    return

def check_if_speaking() -> bool:
    return is_speaking

def set_speaking(set: bool):
    global is_speaking
    is_speaking = set

def force_cut_voice():
    global cut_voice
    cut_voice = True
