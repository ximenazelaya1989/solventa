import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ReporteRegulatorio } from './entities/reporte-regulatorio.entity';

@Module({
  imports: [TypeOrmModule.forFeature([ReporteRegulatorio])],
})
export class ReporteriaModule {}
