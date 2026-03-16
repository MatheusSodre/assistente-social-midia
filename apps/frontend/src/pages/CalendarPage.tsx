import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { Business, ScheduledPost } from '../services/api'

const MONTHS = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]
const DAYS_OF_WEEK = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay()
}

export function CalendarPage() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth()) // 0-indexed
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState('')
  const [scheduledPosts, setScheduledPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedDay, setSelectedDay] = useState<number | null>(null)
  const [scheduleModal, setScheduleModal] = useState(false)
  const [pendingDrafts, setPendingDrafts] = useState<any[]>([])
  const [scheduleForm, setScheduleForm] = useState({ draft_id: '', time: '09:00' })
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.listBusinesses().then(setBusinesses).catch(console.error)
  }, [])

  useEffect(() => {
    if (!selectedBusiness) return
    setLoading(true)
    Promise.all([
      api.calendar(month + 1, year),
      api.listDrafts('approved'),
    ])
      .then(([posts, drafts]) => {
        setScheduledPosts(posts.filter(p => p.business_name === businesses.find(b => b.id === selectedBusiness)?.name))
        setPendingDrafts(drafts.filter((d: any) => d.business_id === selectedBusiness))
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedBusiness, month, year])

  const prevMonth = () => {
    if (month === 0) { setMonth(11); setYear(y => y - 1) }
    else setMonth(m => m - 1)
  }

  const nextMonth = () => {
    if (month === 11) { setMonth(0); setYear(y => y + 1) }
    else setMonth(m => m + 1)
  }

  const getPostsForDay = (day: number) => {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    return scheduledPosts.filter(p => p.scheduled_for?.startsWith(dateStr))
  }

  const handleSchedule = async () => {
    if (!scheduleForm.draft_id || !selectedDay) return
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(selectedDay).padStart(2, '0')}T${scheduleForm.time}:00`
    try {
      await api.schedulePost({ draft_id: scheduleForm.draft_id, scheduled_for: dateStr })
      setMsg('Post agendado!')
      setScheduleModal(false)
      // Refresh
      const posts = await api.calendar(month + 1, year)
      setScheduledPosts(posts.filter(p => p.business_name === businesses.find(b => b.id === selectedBusiness)?.name))
    } catch (e: any) {
      setMsg(`Erro: ${e.message}`)
    }
  }

  const daysInMonth = getDaysInMonth(year, month)
  const firstDay = getFirstDayOfMonth(year, month)
  const cells: (number | null)[] = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
  // Pad to full weeks
  while (cells.length % 7 !== 0) cells.push(null)

  return (
    <div>
      {msg && (
        <div className="alert alert-success alert-dismissible">
          {msg}
          <button type="button" className="close" onClick={() => setMsg('')}>&times;</button>
        </div>
      )}

      <div className="row mb-3">
        <div className="col-md-4">
          <select
            className="form-control"
            value={selectedBusiness}
            onChange={e => setSelectedBusiness(e.target.value)}
          >
            <option value="">Selecione um business...</option>
            {businesses.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>
        <div className="col-md-4 d-flex align-items-center">
          <button className="btn btn-sm btn-outline-secondary mr-2" onClick={prevMonth}>
            <i className="fas fa-chevron-left" />
          </button>
          <strong className="mx-3" style={{ minWidth: 140, textAlign: 'center' }}>
            {MONTHS[month]} {year}
          </strong>
          <button className="btn btn-sm btn-outline-secondary ml-2" onClick={nextMonth}>
            <i className="fas fa-chevron-right" />
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-4">
          <div className="spinner-border text-primary" />
        </div>
      )}

      {!loading && (
        <div className="card">
          <div className="card-body p-0">
            <table className="table table-bordered mb-0" style={{ tableLayout: 'fixed' }}>
              <thead className="thead-light">
                <tr>
                  {DAYS_OF_WEEK.map(d => (
                    <th key={d} className="text-center small py-2" style={{ width: '14.28%' }}>{d}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: cells.length / 7 }, (_, week) => (
                  <tr key={week}>
                    {cells.slice(week * 7, week * 7 + 7).map((day, col) => {
                      const isToday = day === today.getDate() && month === today.getMonth() && year === today.getFullYear()
                      const posts = day ? getPostsForDay(day) : []
                      return (
                        <td
                          key={col}
                          style={{
                            height: 100,
                            verticalAlign: 'top',
                            background: isToday ? '#e8f4fd' : day ? '#fff' : '#f9f9f9',
                            cursor: day && selectedBusiness ? 'pointer' : 'default',
                          }}
                          onClick={() => {
                            if (day && selectedBusiness) {
                              setSelectedDay(day)
                              setScheduleModal(true)
                              setScheduleForm({ draft_id: '', time: '09:00' })
                            }
                          }}
                        >
                          {day && (
                            <>
                              <div className={`small font-weight-bold mb-1 ${isToday ? 'text-primary' : 'text-muted'}`}>
                                {day}
                              </div>
                              {posts.map(p => (
                                <div
                                  key={p.id}
                                  className="badge badge-info mb-1 d-block text-truncate"
                                  style={{ fontSize: 10 }}
                                  title={p.caption}
                                >
                                  <i className={`fas fa-${p.format === 'story' ? 'image' : p.format === 'reel' ? 'film' : 'th'} mr-1`} />
                                  {p.caption?.substring(0, 20)}…
                                </div>
                              ))}
                            </>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!selectedBusiness && (
        <div className="text-center text-muted mt-4">
          <i className="fas fa-calendar-alt fa-3x mb-2" style={{ opacity: 0.3 }} />
          <p>Selecione um business para ver o calendário editorial.</p>
        </div>
      )}

      {/* Schedule Modal */}
      {scheduleModal && (
        <div className="modal fade show" style={{ display: 'block', background: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Agendar post para {selectedDay}/{month + 1}/{year}
                </h5>
                <button type="button" className="close" onClick={() => setScheduleModal(false)}>&times;</button>
              </div>
              <div className="modal-body">
                <div className="form-group">
                  <label>Selecionar rascunho aprovado</label>
                  <select
                    className="form-control"
                    value={scheduleForm.draft_id}
                    onChange={e => setScheduleForm(f => ({ ...f, draft_id: e.target.value }))}
                  >
                    <option value="">Selecione...</option>
                    {pendingDrafts.map((d: any) => (
                      <option key={d.id} value={d.id}>
                        [{d.format}] {(d.caption || '').substring(0, 60)}...
                      </option>
                    ))}
                  </select>
                  {pendingDrafts.length === 0 && (
                    <small className="text-muted">Nenhum rascunho aprovado disponível</small>
                  )}
                </div>
                <div className="form-group">
                  <label>Horário</label>
                  <input
                    type="time"
                    className="form-control"
                    value={scheduleForm.time}
                    onChange={e => setScheduleForm(f => ({ ...f, time: e.target.value }))}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setScheduleModal(false)}>Cancelar</button>
                <button
                  className="btn btn-primary"
                  onClick={handleSchedule}
                  disabled={!scheduleForm.draft_id}
                >
                  <i className="fas fa-calendar-check mr-1" /> Agendar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
