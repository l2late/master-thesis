%     This program computes the internal heat gains derived from occupants
%     in an office building by use of a Markov chain.
%
%     Copyright (C) 2021  Mathias Hudoba de Badyn
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

clear all; close all; clc;

% this script tests and generates the occupant disturbances

% main hallway is room 3

nRooms = 5;
nPeople = 15;
nDays = 4;

% discretize in 15 minute increments
dt = 0.25;
t_space_dist = 0:dt:(24-dt);

states = nRooms + 1; % state 6 is the "go home" state

% come to work by entering hallway

P1 = [0.5 0.3 0.2 0   0   0;
      0.2 0.6 0.2 0   0   0;
      0.2 0.3 0.2 0.3 0   0;  
      0   0   0.1 0.7 0.2 0;
      0   0   0.1 0.2 0.7 0;
      0   0   1   0   0   0]; 


% do work - also uses P1


% go to lunch - leave via hallway

P2 = [0.1 0   0.9 0   0   0;
      0   0.1 0.9 0   0   0;
      0   0   0.1 0   0   0.9;  
      0   0   0.9 0.1 0   0;
      0   0   0.9 0   0.1 0;
      0   0   0   0   0   1]; 


% do work again - use P1
% start going home - use P2
% stay home - don't need to simulate this


% simulate one day by propagating PMF

p0 = [0; 0; 0; 0; 0; 1]; % everyone starts outside the office

p_array = zeros(6,length(t_space_dist));

% simulate a rather dystopic typical office work day
for ii = 1:length(t_space_dist)
    
    t = t_space_dist(ii);
    
    if t<8
        % people out of office
        p_array(:,ii) = p0;
    elseif t<= 12
        % people start coming to the office and working
        p_array(:,ii) = P1'*p_array(:,ii-1);
    elseif t<= 13.5
        % people go out for lunch
        p_array(:,ii) = P2'*p_array(:,ii-1);
    elseif t<= 17
        % people come back and work
        p_array(:,ii) = P1'*p_array(:,ii-1);
    elseif t<= 18
        % people start to go home
        p_array(:,ii) = P2'*p_array(:,ii-1);
    else
        % people are all home
        p_array(:,ii) = p0;
    end
end
        

internalHeatGain.p_array = p_array;
internalHeatGain.t_space_dist = t_space_dist;


save('ihg_model.mat', 'internalHeatGain');

