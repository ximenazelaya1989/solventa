import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { SocioDistribucion } from '../../cotizacion/entities/socio-distribucion.entity';

// TODO(cotizacion/integraciones): aplicar con @UseGuards(ApiKeyGuard) en los
// controladores de socios (HU5.1.1) cuando el dueño del modulo los defina.
// No esta aplicado a ningun controlador todavia -- en particular no se toco
// src/cotizacion (rating engine pendiente de merge en
// origin/feature/hu112-rolling-update-reglas-rating).
@Injectable()
export class ApiKeyGuard implements CanActivate {
  constructor(
    @InjectRepository(SocioDistribucion)
    private readonly socioDistribucionRepository: Repository<SocioDistribucion>,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-api-key'];
    if (!apiKey) {
      throw new UnauthorizedException('Falta la cabecera x-api-key');
    }

    const socio = await this.socioDistribucionRepository.findOneBy({
      apiKey,
    });
    if (!socio) {
      throw new UnauthorizedException('apiKey invalida');
    }

    request.socioDistribucion = socio;
    return true;
  }
}
