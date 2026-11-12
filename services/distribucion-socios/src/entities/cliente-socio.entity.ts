import { Column, Entity, Index, PrimaryGeneratedColumn } from 'typeorm';

// EXP-010 (HU5.1.1, Génesis). Tabla nueva: que clientes pertenecen a cada socio.
// Se usa para la tactica "autorizar actores" por pertenencia: un socio solo
// puede pedir cotizaciones para sus propios clientes.
@Entity('clientes_socio')
@Index(['socioId', 'clienteId'], { unique: true })
export class ClienteSocio {
  @PrimaryGeneratedColumn('uuid')
  id!: string;

  @Column({ type: 'uuid' })
  socioId!: string;

  @Column({ type: 'uuid' })
  clienteId!: string;
}
