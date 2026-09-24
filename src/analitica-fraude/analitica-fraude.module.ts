import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MotorDeteccionFraude } from './entities/motor-deteccion-fraude.entity';
import { AnaliticaFraudeService } from './analitica-fraude.service';
import { AnaliticaFraudeController } from './analitica-fraude.controller';
import { PagosModule } from '../pagos/pagos.module';

@Module({
  imports: [TypeOrmModule.forFeature([MotorDeteccionFraude]), PagosModule],
  controllers: [AnaliticaFraudeController],
  providers: [AnaliticaFraudeService],
  exports: [AnaliticaFraudeService],
})
export class AnaliticaFraudeModule {}
