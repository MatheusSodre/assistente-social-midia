import { useAuth } from '../contexts/AuthContext'

export function AdminLTEHome() {
  const { usuario } = useAuth()

  return (
    <div className="row">
      <div className="col-12">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Bem-vindo, {usuario?.nome}</h3>
          </div>
          <div className="card-body">
            <p>Selecione um módulo no menu lateral para começar.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
