%     Copyright (C) 2021, ETH Zurich [Dominic Liao-McPherson]
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.

clear all
close all
clc



tstop = 8;

ts = 0.5; % sampling period

N = 4; % number of agents
nx = 3; % state dimension
nu = 2; % input dimension


% feedback gains
K = [1;0.5];

% target positions
ubar = [-4,-12,1,16;
        -8,-3,7,8];

% initial condition
x0 = zeros(nx,N);
% give some zero orientations errors
x0(3,:) = [pi/2,-pi/2,pi,pi/4]; 

% input constraints
umax = [10;6];
umin = [-5;-6];

% cost weighting parameter
c = 0.25;
% c = 1;

% Solve for the static NE a-priori
kmax = 100;
une = zeros(nu,N);
for i = 1:kmax
  for j = 1:N
    une(:,j) = best_response(ubar(:,j),une,j,c,umax,umin);
  end
end

xne = [une;zeros(1,N)];

out = sim('game_example.slx');




X = out.x.Data;
t = out.x.Time;


figure();


for j = 1:N
  x = squeeze(X(1,j,:));
  y = squeeze(X(2,j,:));

  plot(x,y);
  hold on
end
% add a box to the plot
% rectangle('position',[xmin ymin xmin xmax])
h = rectangle('position',[umin' umax(1)-umin(1) umax(2)-umin(2)],'LineWidth',2);

% plot sources and GNE solutions
for j = 1:N
  h1 = plot(ubar(1,j),ubar(2,j),'bx');
  h2 = plot(une(1,j),une(2,j),'ro');
end
legend([h1,h2],{'Sources','NE Solution'});
xlabel('a');
ylabel('b');


figure();
ylab = {'$a - \bar{a}$','$b - \bar{b}$','$\phi$'};
for i = 1:nx-1
  subplot(2,2,i);
  for j = 1:N
    plot(t,squeeze(X(i,j,:)) - xne(i,j));
    hold on
  end
  axis tight
  ylabel(ylab{i},'interpreter','latex')
end

subplot(2,2,2);
U = out.u.Data;
o = ones(size(t));

ulab = {'$u_a$','$u_b$'};
for i = 1:nu
  subplot(2,2,2+i);
  for j = 1:N
    plot(t,squeeze(U(i,j,:)));
    hold on

  end
  h = plot(t,o*umax(i),'k--');
  plot(t,o*umin(i),'k--');

  axis tight
  ylabel(ulab{i},'interpreter','latex');
  xlabel('Time [s]');
end
legend(h,'Constraints');





% "Exact" solution of the IVP for a single agent
function xp = fd(ts,x,u,k)
  f = @(t,x) agent_dynamics(x,u,k);
  [t,x] = ode45(f,[0,ts],x);
  xp = x(end,:)';
end

