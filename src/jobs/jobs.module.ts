import { Module } from '@nestjs/common';
import { JobsService } from './jobs.service';
import { PerfilamientoModule } from '../perfilamiento/perfilamiento.module';
import { ReaseguroModule } from '../reaseguro/reaseguro.module';
import { ReporteriaModule } from '../reporteria/reporteria.module';

@Module({
  imports: [PerfilamientoModule, ReaseguroModule, ReporteriaModule],
  providers: [JobsService],
  exports: [JobsService],
})
export class JobsModule {}
