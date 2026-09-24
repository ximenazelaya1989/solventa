import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ReporteRegulatorio } from './entities/reporte-regulatorio.entity';
import { ReporteriaService } from './reporteria.service';
import { ReporteriaController } from './reporteria.controller';
import { PolizasModule } from '../polizas/polizas.module';

@Module({
  imports: [TypeOrmModule.forFeature([ReporteRegulatorio]), PolizasModule],
  controllers: [ReporteriaController],
  providers: [ReporteriaService],
  exports: [ReporteriaService],
})
export class ReporteriaModule {}
