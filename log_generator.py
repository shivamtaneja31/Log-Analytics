import random
import time
from datetime import datetime
from typing import Dict, List

class LogGenerator:
    def __init__(self):
        self.services = ["web-server", "database", "auth-service", "payment-service", "user-service"]
        self.normal_messages = [
            "Request processed successfully",
            "Database query completed",
            "Cache hit",
            "User session validated",
            "Payment transaction completed"
        ]
        self.warning_messages = [
            "High CPU usage detected",
            "Memory usage above 80%",
            "Slow database query detected",
            "Cache miss occurred",
            "API rate limit approaching threshold"
        ]
        self.error_messages = [
            "Database connection failed",
            "Authentication token expired",
            "Payment processing failed",
            "Internal server error",
            "API rate limit exceeded"
        ]
        self.error_codes = ["ERR001", "ERR002", "ERR003", "ERR004", "ERR005"]

    def generate_stack_trace(self, error_message: str) -> str:
        return f"""Exception: {error_message}
    at Service.processRequest (/services/main.py:42:18)
    at async Handler.execute (/handlers/base.py:120:22)
    at async Server.handleRequest (/server/core.py:88:12)"""

    def generate_normal_log(self) -> Dict:
        service = random.choice(self.services)
        return {
            "level": "INFO",
            "service": service,
            "message": random.choice(self.normal_messages),
            "error_code": None,
            "stack_trace": None
        }

    def generate_warning_log(self) -> Dict:
        service = random.choice(self.services)
        return {
            "level": "WARNING",
            "service": service,
            "message": random.choice(self.warning_messages),
            "error_code": None,
            "stack_trace": None
        }

    def generate_error_log(self) -> Dict:
        service = random.choice(self.services)
        message = random.choice(self.error_messages)
        return {
            "level": "ERROR",
            "service": service,
            "message": message,
            "error_code": random.choice(self.error_codes),
            "stack_trace": self.generate_stack_trace(message)
        }

    def generate_anomaly_metrics(self) -> Dict:
        metrics = {
            "error_rate": random.uniform(0, 0.1),
            "response_time": random.uniform(100, 500),
            "cpu_usage": random.uniform(20, 95),
            "memory_usage": random.uniform(30, 90)
        }
        return metrics

    def generate_burst_errors(self, count: int) -> List[Dict]:
        """Generate a burst of error logs to simulate an incident"""
        service = random.choice(self.services)
        error_message = random.choice(self.error_messages)
        error_code = random.choice(self.error_codes)
        
        burst_logs = []
        for _ in range(count):
            log = {
                "level": "ERROR",
                "service": service,
                "message": error_message,
                "error_code": error_code,
                "stack_trace": self.generate_stack_trace(error_message)
            }
            burst_logs.append(log)
        return burst_logs

    def simulate_normal_traffic(self) -> Dict:
        """Simulate normal traffic with occasional warnings"""
        rand = random.random()
        if rand < 0.8:  # 80% normal logs
            return self.generate_normal_log()
        elif rand < 0.95:  # 15% warning logs
            return self.generate_warning_log()
        else:  # 5% error logs
            return self.generate_error_log()

    def simulate_incident(self) -> List[Dict]:
        """Simulate an incident with burst errors and related warnings"""
        logs = []
        # Generate warning signs
        for _ in range(2):
            logs.append(self.generate_warning_log())
        
        # Generate burst of errors
        logs.extend(self.generate_burst_errors(5))
        
        return logs
