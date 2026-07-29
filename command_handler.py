import json
import serial
import time
def parse_command_payload(payload_text):
    try:
        command_data=json.loads(payload_text)
    except json.JSONDecodeError:
        print("invalid command json")
        return None
    if not isinstance(command_data,dict):
        print("command must be an object")
        return None
    command=command_data.get("command")
    if not isinstance(command,str):
        print("command must be a string")
        return None
    command=command.strip()
    if command == "":
        print("command cannot be empty")
        return None
    return command
def execute_command(command):
    if command == "led_on":
        print("simulated actuator: LED ON")
        return True

    elif command == "led_off":
        print("simulated actuator: LED OFF")
        return True

    else:
        print("unsupported command:", command)
        return False
def build_command_ack(command, status):
    if not isinstance(command,str):
        raise TypeError(f"command type must be str")
    command=command.strip()
    if not command:
        raise ValueError(f"command can not be empty")
    if not isinstance(status,str):
        raise TypeError(f"status must be str:{status}")
    status=status.strip()
    if status not in ("success","failed","timeout"):
        raise ValueError(f"status value is not admitted:{status}")
    ack_data = {
        "command": command,
        "status": status
    }
    return json.dumps(ack_data)
def send_command_to_serial(ser, command):
    if ser is None:
        print(f"ser is not exist:{ser}")
        return False
    if not  ser.is_open:
        print(f"ser is not open:{ser}")
        return False
    if not isinstance(command,str):
        print(f"command is not str:{command}")
        return False
    command = command.strip()
    if command =="":
        print(f"command can not be empty")
        return False
    if command not in ("led_on", "led_off"):
        print(f"unsupported serial command: {command}")
        return False
    right_command=command+"\r\n"
    command_bytes=right_command.encode("utf-8")
    try:
        written_bytes = ser.write(command_bytes)

        if written_bytes != len(command_bytes):
            print(f"serial partial write: "f"written={written_bytes}, "f"expected={len(command_bytes)}")
            return False

        print(f"command forwarded to serial: {command}")
        return True

    except serial.SerialTimeoutException as e:
        print(f"serial write timeout: {e}")
        return False

    except serial.SerialException as e:
        print(f"serial write failed: {e}")
        return False
def parse_stm32_ack(serial_data):
    right_ack={}
    if not isinstance(serial_data, str):
        return None
    serial_data=serial_data.strip()
    parts=serial_data.split(":")
    if len(parts)!=3:
        return None
    if parts[0]=="ack" and parts[1]!="" and parts[2] in ("success","failed"):
        right_ack["command"]=parts[1]
        right_ack["status"]=parts[2]
    else:
        return None
    return right_ack
def check_command_ack_timeout(command_state, timeout_seconds):
    with command_state["lock"]:
        pending_command=command_state["pending_command"]
        pending_since=command_state["pending_since"]
        if pending_command is None:
            return None
        if pending_since is None:
            return None
        else:
            elapsed=time.monotonic()-pending_since
        if elapsed >=timeout_seconds:
            command=pending_command
            command_state["pending_command"]=None
            command_state["pending_since"]=None
        else:
            return None
    return command