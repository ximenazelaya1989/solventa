import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Cotizacion } from './entities/cotizacion.entity';
import { Producto } from './entities/producto.entity';
import { SocioDistribucion } from './entities/socio-distribucion.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Cotizacion, Producto, SocioDistribucion])],
})
export class CotizacionModule {}