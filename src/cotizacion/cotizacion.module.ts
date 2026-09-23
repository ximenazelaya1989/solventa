import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Cotizacion } from './entities/cotizacion.entity';
import { Producto } from './entities/producto.entity';
import { SocioDistribucion } from './entities/socio-distribucion.entity';
import { ReglaRating } from './entities/regla-rating.entity';
import { RatingService } from './rating.service';
import { RatingController } from './rating.controller';
import { CotizacionService } from './cotizacion.service';
import { CotizacionController } from './cotizacion.controller';

@Module({
  imports: [
    TypeOrmModule.forFeature([Cotizacion, Producto, SocioDistribucion, ReglaRating]),
  ],
  controllers: [RatingController, CotizacionController],
  providers: [RatingService, CotizacionService],
})
export class CotizacionModule {}