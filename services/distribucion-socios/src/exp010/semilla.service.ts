import { Injectable, OnApplicationBootstrap } from '@nestjs/common';
import { randomBytes } from 'crypto';
import { DataSource } from 'typeorm';
import { ClienteSocio } from '../entities/cliente-socio.entity';
import { CredencialSocio } from '../entities/credencial-socio.entity';
import { SocioDistribucion } from '../entities/socio-distribucion.entity';
import {
  CLIENTE_SOCIO_A,
  CLIENTE_SOCIO_B,
  CLIENTES_COGNITO_SOCIO_A,
  CLIENTES_COGNITO_SOCIO_B,
  EXP010_ACTIVO,
  SOCIO_A,
  SOCIO_B,
  registrar,
} from './exp010.config';

// EXP-010: carga los datos de prueba (idempotente). Solo corre con
// JWT_VALIDATION_ENABLED=true, asi la base compartida no cambia.
@Injectable()
export class SemillaExp010Service implements OnApplicationBootstrap {
  constructor(private readonly ds: DataSource) {}

  async onApplicationBootstrap() {
    if (!EXP010_ACTIVO) return;

    const socios = this.ds.getRepository(SocioDistribucion);
    const credenciales = this.ds.getRepository(CredencialSocio);
    const clientes = this.ds.getRepository(ClienteSocio);

    const plan = [
      { socioId: SOCIO_A, canal: 'Socio A (prueba EXP-010)', clienteId: CLIENTE_SOCIO_A, cognito: CLIENTES_COGNITO_SOCIO_A },
      { socioId: SOCIO_B, canal: 'Socio B (prueba EXP-010)', clienteId: CLIENTE_SOCIO_B, cognito: CLIENTES_COGNITO_SOCIO_B },
    ];

    for (const p of plan) {
      if (!(await socios.findOneBy({ id: p.socioId }))) {
        // apiKey es un dato sensible de la base; aqui solo se rellena con un
        // valor aleatorio porque la autenticacion del EXP-010 es por JWT.
        await socios.save({ id: p.socioId, canal: p.canal, apiKey: randomBytes(24).toString('hex') });
      }
      if (!(await clientes.findOneBy({ socioId: p.socioId, clienteId: p.clienteId }))) {
        await clientes.save({ socioId: p.socioId, clienteId: p.clienteId });
      }
      for (const cognitoClientId of p.cognito) {
        const existente = await credenciales.findOneBy({ cognitoClientId });
        if (!existente) {
          await credenciales.save({ socioId: p.socioId, cognitoClientId });
        } else if (existente.socioId !== p.socioId) {
          existente.socioId = p.socioId;
          await credenciales.save(existente);
        }
      }
    }
    registrar('semilla_cargada', {
      socios: plan.map((p) => ({ socioId: p.socioId, clienteId: p.clienteId, apps: p.cognito.length })),
    });
  }
}
