import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';
import { numericTransformer } from '../../common/transformers/numeric.transformer';

export enum TipoPago {
  COBRO_PRIMA = 'cobro_prima',
  INDEMNIZACION = 'indemnizacion',
}

export enum EstadoPago {
  PENDIENTE = 'pendiente',
  BLOQUEADO = 'bloqueado',
  PROCESADO = 'procesado',
  FALLIDO = 'fallido',
}

@Entity('pagos')
export class Pago {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'enum', enum: TipoPago })
  tipo!: TipoPago;

  @Column({ type: 'numeric', transformer: numericTransformer })
  monto!: number;

  @Column({ type: 'varchar' })
  moneda!: string; // ej. USD

  @Column({
    type: 'enum',
    enum: EstadoPago,
    default: EstadoPago.PENDIENTE,
  })
  estado!: EstadoPago;

  @Column({ type: 'varchar', unique: true })
  claveIdempotencia!: string; // evita duplicar o perder el pago

  @Column({ type: 'uuid', nullable: true })
  polizaId!: string | null;

  @Column({ type: 'uuid', nullable: true })
  siniestroId!: string | null;

  @Column({ type: 'timestamptz', nullable: true })
  fechaProcesado!: Date | null;
}
