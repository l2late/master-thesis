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


x0 = [0.1;0.1;pi/2];


u = [1;1];

k = [1;0.5];


f = @(t,x) agent_dynamics(x,u,k);
t0 = 0;
tf = 15;

[t,x] = ode45(f,[t0,tf],x0);

y = x(:,2);
p = x(:,3);
x = x(:,1);

figure();
subplot(2,1,1);
plot(t,x,t,y);
subplot(2,1,2);
plot(x,y);

% subplot(2,1,1);
% plot()

