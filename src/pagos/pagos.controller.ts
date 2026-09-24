import { Body, Controller, Post } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { PagosService } from './pagos.service';
import { CrearDesembolsoDto } from './dto/crear-desembolso.dto';
import { Pago } from './entities/pago.entity';

@Controller('desembolsos')
export class PagosController {
  constructor(
    private readonly pagosService: PagosService,
    @InjectDataSource() private readonly dataSource: DataSource,
  ) {}

  @Post()
  crear(@Body() datos: CrearDesembolsoDto): Promise<Pago> {
    return this.dataSource.transaction((manager) =>
      this.pagosService.pagarIndemnizacion(
        manager,
        datos.siniestroId,
        datos.monto,
      ),
    );
  }
}
