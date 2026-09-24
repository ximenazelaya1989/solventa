import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  OneToOne,
  VersionColumn,
} from 'typeorm';
import { Suscripcion } from '../../suscripcion/entities/suscripcion.entity';

export enum EstadoPoliza {
  PENDIENTE = 'pendiente',
  EMITIDA = 'emitida',
  RENOVADA = 'renovada',
  CANCELADA = 'cancelada',
}

@Entity('polizas')
export class Poliza {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'enum', enum: EstadoPoliza, default: EstadoPoliza.PENDIENTE })
  estado!: EstadoPoliza;

  @Column({ type: 'uuid' })
  clienteId!: string;

  @Column({ type: 'uuid' })
  productoId!: string;

  @VersionColumn()
  version!: number;

  @OneToOne(() => Suscripcion, (s) => s.poliza)
  suscripcion!: Suscripcion;
}