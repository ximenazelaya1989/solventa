import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  Index,
} from 'typeorm';
import { numericTransformer } from '../common/numeric.transformer';

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

  // EXP-006 (H7.2.1): la restriccion UNIQUE es la tactica de idempotencia.
  // Si dos replicas reciben el mismo pago a la vez, solo una puede insertarlo.
  @Column({ type: 'varchar', unique: true })
  claveIdempotencia!: string; // evita duplicar o perder el pago

  @Column({ type: 'uuid', nullable: true })
  polizaId!: string | null;

  @Index()
  @Column({ type: 'uuid', nullable: true })
  siniestroId!: string | null;

  @Column({ type: 'varchar', nullable: true })
  referenciaPasarela!: string | null; // id de la transaccion en la pasarela

  @Column({ type: 'varchar', nullable: true })
  atendidoPor!: string | null; // replica (host y zona) que proceso el pago

  @CreateDateColumn({ type: 'timestamptz' })
  fechaCreacion!: Date;

  @Column({ type: 'timestamptz', nullable: true })
  fechaProcesado!: Date | null;
}
