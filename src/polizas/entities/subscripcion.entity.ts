import { Entity, PrimaryGeneratedColumn, Column, OneToOne } from 'typeorm';
import { Poliza } from './poliza.entity';

@Entity('subscripciones')
export class Subscripcion {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  decision!: string;

  @OneToOne(() => Poliza, (p) => p.subscripcion)
  poliza!: Poliza;
  
}