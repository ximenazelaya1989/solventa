import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity('reaseguradoras')
export class Reaseguradora {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'varchar' })
  nombre!: string;

  @Column({ type: 'varchar', unique: true })
  codigo!: string;
}
