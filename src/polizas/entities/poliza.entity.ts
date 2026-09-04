import { Entity, PrimaryGeneratedColumn, Column, OneToOne, JoinColumn } from 'typeorm';
import { Subscripcion } from '../../suscripcion/entities/subscripcion.entity';

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
  cotizacionId!: string; 

  @Column({ type: 'uuid' })
  productoId!: string;

  @OneToOne(() => Subscripcion, (s) => s.poliza, { cascade: true })
  @JoinColumn()
  subscripcion!: Subscripcion;

}