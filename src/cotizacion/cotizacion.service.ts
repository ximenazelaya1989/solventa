import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Cotizacion } from './entities/cotizacion.entity';
import { Producto } from './entities/producto.entity';
import { RatingService } from './rating.service';
import { CrearCotizacionDto } from './dto/crear-cotizacion.dto';

@Injectable()
export class CotizacionService {
  constructor(
    @InjectRepository(Cotizacion)
    private readonly cotizacionRepository: Repository<Cotizacion>,
    @InjectRepository(Producto)
    private readonly productoRepository: Repository<Producto>,
    private readonly ratingService: RatingService,
  ) {}

  async cotizar(datos: CrearCotizacionDto): Promise<Cotizacion> {
    if (!this.ratingService.estaSaludable()) {
      // En produccion el ALB ya habria sacado esta instancia de rotacion
      // antes de que una peticion real llegue hasta aqui.
      throw new ServiceUnavailableException(
        'El motor de rating de esta instancia no tiene una version sana cargada',
      );
    }

    const producto = await this.productoRepository.findOneByOrFail({ id: datos.productoId });
    const prima = this.ratingService.calcularPrima(producto.prima, datos.nivelRiesgo);

    const cotizacion = this.cotizacionRepository.create({
      prima,
      clienteId: datos.clienteId,
      productoId: datos.productoId,
      socioDistribucionId: datos.socioDistribucionId ?? null,
    });

    return this.cotizacionRepository.save(cotizacion);
  }
}