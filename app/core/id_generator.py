from app.core.storage import Storage

class IDGenerator:
    @staticmethod
    def generate(prefix: str) -> str:
        """
        Generates a sequential ID like DPT-01, EMP-02, ADM-01.
        Tracks counters in a centralized 'counters.json' file.
        """
        counters = Storage.load("counters")
        
        # Initialize counter for this prefix if it doesn't exist
        if prefix not in counters:
            counters[prefix] = 0
            
        counters[prefix] += 1
        Storage.save("counters", counters)
        
        # Format with leading zero (e.g., 01, 02... 10, 11)
        return f"{prefix}-{counters[prefix]:02d}"