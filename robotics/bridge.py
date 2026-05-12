from loguru import logger

class BAYMAXRoboticsBridge:
    SUPPORTED_COMMANDS = ["move", "speak", "scan", "grip", "release"]

    def send_command(self, command: str, params: dict = None) -> dict:
        if command not in self.SUPPORTED_COMMANDS:
            logger.error(f"Unknown robotics command: {command}")
            return {"error": f"Unknown command: {command}"}
            
        params = params or {}
        logger.info(f"Dispatched robotics command: {command} with params: {params}")
        
        return {
            "status": "dispatched",
            "command": command,
            "params": params
        }

    def status(self) -> dict:
        return {
            "connected": False,
            "mode": "stub",
            "system": "BAYMAX-Robotics-v1"
        }