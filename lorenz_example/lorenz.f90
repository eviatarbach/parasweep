program lorenz

real(8), parameter :: dt = 1e-4, d0 = 1e-8
integer, parameter :: N_spin = 1000000, N_run = 1000000
real(8) :: beta, sigma, rho, x_a, y_a, z_a, x_b, y_b, z_b, d1, lyap = 0
integer :: i
namelist /params/ beta, sigma, rho
character(6) :: sim_id

call get_command_argument(1, sim_id)
open(1, file="params_" // trim(sim_id) // ".nml")
read(1, nml=params)

! Spin-up
x_a = 1; y_a = 1; z_a = 1
do i = 1, N_spin
  call integrate(x_a, y_a, z_a)
end do

! Choose point a distance of d0 away
x_b = x_a + d0/sqrt(3.)
y_b = y_a + d0/sqrt(3.)
z_b = z_a + d0/sqrt(3.)

! Calculate largest Lyapunov exponent
do i = 1, N_run
  call integrate(x_a, y_a, z_a)
  call integrate(x_b, y_b, z_b)

  d1 = norm2((/ x_a, y_a, z_a /) - (/ x_b, y_b, z_b /))
  lyap = lyap + log(abs(d1/d0))

  ! Rescale
  x_b = x_a + d0*(x_b - x_a)/d1
  y_b = y_a + d0*(y_b - y_a)/d1
  z_b = z_a + d0*(z_b - z_a)/d1
end do

lyap = lyap/(N_run*dt)

open(2, file="results_" // trim(sim_id) // ".txt", action="write")
write(2, *) lyap

contains
  subroutine integrate(x, y, z)
    ! Integrate using midpoint method
    real(8), intent(inout) :: x, y, z
    real(8) :: x_temp, y_temp, z_temp
    x_temp = x + dt*sigma*(y - x)/2
    y_temp = y + dt*(x*(rho - z) - y)/2
    z_temp = z + dt*(x*y - beta*z)/2
    x = x + dt*sigma*(y_temp - x_temp)
    y = y + dt*(x_temp*(rho - z_temp) - y_temp)
    z = z + dt*(x_temp*y_temp - beta*z_temp)
  end subroutine
end program
