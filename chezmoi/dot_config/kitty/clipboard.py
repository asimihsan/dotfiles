from kittens.tui.handler import result_handler
import subprocess

def main(args):
    # This is required for kitty kittens
    pass

def is_nvim_focused():
    try:
        return subprocess.check_output(['ps', '-p', '$PPID', '-o', 'comm=']).decode().strip() == 'nvim'
    except:
        return False

@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    if is_nvim_focused():
        w = boss.window_id_map.get(target_window_id)
        if w is not None:
            w.write_to_child(b'\x06')  # Ctrl+F
    else:
        boss.copy_to_clipboard()
