import { IsNumber, IsPositive, IsUUID } from 'class-validator';

export class CrearDesembolsoDto {
  @IsUUID()
  siniestroId!: string;

  @IsNumber({ maxDecimalPlaces: 2 })
  @IsPositive()
  monto!: number;
}
