class Tools():
    @staticmethod
    def _request_vacation(days:int, start_date:str) -> str:
        """
        Simulates a vacation request process.

        Args:
            days (int): Number of vacation days requested.
            start_date (str): Start date for the vacation in 'YYYY-MM-DD' format.

        Returns:
            str: Confirmation message of the vacation request.
        """
        return f"Solicitud de vacaciones de {days} dias emepezando en {start_date} ha sido enviada."
    
