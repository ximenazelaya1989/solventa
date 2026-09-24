import { Type } from 'class-transformer';
import {
  IsNumber,
  IsObject,
  IsUUID,
  Max,
  Min,
  ValidateNested,
} from 'class-validator';

export class SeñalesOpenDataDto {
  @IsNumber()
  @Min(0)
  ingresoMensual!: number;

  @IsNumber()
  @Min(0)
  deudaTotal!: number;

  @IsNumber()
  @Min(0)
  @Max(1)
  indicePago!: number;
}

export class ReprocesarPerfilDto {
  @IsUUID()
  clienteId!: string;

  @IsObject()
  @ValidateNested()
  @Type(() => SeñalesOpenDataDto)
  señalesOpenData!: SeñalesOpenDataDto;
}
