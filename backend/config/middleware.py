"""
Middleware customizado para validar hosts do Railway dinamicamente.
Deve ser colocado ANTES do CommonMiddleware para interceptar a validação de host.
"""
from django.core.exceptions import DisallowedHost
from django.http import HttpRequest


class RailwayHostValidationMiddleware:
    """
    Middleware que permite qualquer domínio .railway.app ou .up.railway.app
    Intercepta a validação de host antes do CommonMiddleware
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Override temporário do método get_host para validar Railway hosts
        original_get_host = request.__class__.get_host
        
        def get_host_with_railway_validation(self):
            """Override get_host para aceitar domínios Railway"""
            host = original_get_host(self)
            host_without_port = host.split(':')[0]
            
            # Se o host termina com .railway.app ou .up.railway.app, permite
            if host_without_port.endswith('.railway.app') or host_without_port.endswith('.up.railway.app'):
                return host
            
            # Caso contrário, usa a validação padrão
            return host
        
        # Aplica o override temporariamente
        request.__class__.get_host = get_host_with_railway_validation
        
        try:
            response = self.get_response(request)
        finally:
            # Restaura o método original
            request.__class__.get_host = original_get_host
        
        return response
