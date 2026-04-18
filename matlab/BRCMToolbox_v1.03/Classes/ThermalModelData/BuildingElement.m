classdef BuildingElement
   %BUILDINGELEMENT This class represents a building element (wall, floor,..), such as construction type, area ...
   % ------------------------------------------------------------------------
   % This file is part of the BRCM Toolbox v1.03.
   %
   % The BRCM Toolbox - Building Resistance-Capacitance Modeling for Model Predictive Control.
   % Copyright (C) 2013  Automatic Control Laboratory, ETH Zurich.
   % 
   % The BRCM Toolbox is free software; you can redistribute it and/or modify
   % it under the terms of the GNU General Public License as published by
   % the Free Software Foundation, either version 3 of the License, or
   % (at your option) any later version.
   % 
   % The BRCM Toolbox is distributed in the hope that it will be useful,
   % but WITHOUT ANY WARRANTY; without even the implied warranty of
   % MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   % GNU General Public License for more details.
   % 
   % You should have received a copy of the GNU General Public License
   % along with the BRCM Toolbox.  If not, see <http://www.gnu.org/licenses/>.
   %
   % For support check www.brcm.ethz.ch.
   % ------------------------------------------------------------------------
   
   
   
   properties(Hidden,Constant)
      n_properties@uint64 = uint64(8);        % number of properties required for an object instance
      key@char = 'B';                       % identifier key, first letter of the identifier, e.g. B0001
   end % properties(Constant,Hidden)
   
       properties (SetAccess = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %properties % IF_NO_METACLASS_SUPPORT
      identifier@char = '';                 % identifier of the building element, e.g. B0001
      description@char = '';                % description of the building element
      construction_identifier@char = '';    % identifier for the construction type (Construction,No mass construction),  e.g. C0001, NMC0001
      adjacent_A@char;                      % identifier for the adjacent side of the buiilding element (zone,ambient,ground,adiabatic or disturbance identifier)
      adjacent_B@char;                      % identifier for the adjacent side of the buiilding element (zone,ambient,ground,adiabatic or disturbance identifier)
      window_identifier@char = '';          % identifier for the window in building element, e.g. W0001
      area@char = '';                       % area of the building element
      vertices;                               % vertices store the building elements vertices coordinates (we also support 'NULL' in order to allow for inconsistency)
   end % properties
   
       methods (Access = {?ThermalModelData}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      % constructor
      function obj = BuildingElement(identifier,description,construction_identifier,adjacent_A,adjacent_B,...
            window_identifier,vertices,area)
         if nargin == obj.n_properties
            obj.identifier = identifier;
            obj.description = description;
            obj.construction_identifier = construction_identifier;
            obj.adjacent_A = adjacent_A;
            obj.adjacent_B = adjacent_B;
            obj.window_identifier = window_identifier;
            obj.vertices = vertices;
            
            if isnumeric(area)
               obj.area = num2str(area,Constants.num2str_precision);
            else
               obj.area = area;
            end
         elseif nargin > 0 && nargin ~= obj.n_properties;
            error('BuildingElement:Constructor','Argument error. %s requires %d arguments for object creation.',Constants.buildingelement_name_str,obj.n_properties);
         end
         
      end % BuildingElement
      
   end % methods(Access = {?ThermalModelData})
   
   methods
      function mat = vertices2Matrix(obj)
         
         n_vertices = length(obj.vertices);
         if n_vertices<1
            mat = [];
            return;
         end
         mat = nan(size(obj.vertices(1).vertex2ColumnVec,1),n_vertices);
         
         for i = 1:n_vertices
            mat(:,i) = obj.vertices(i).vertex2ColumnVec;
         end
         
      end % vertices2Matrix
      
      function tf = isHorizontal(obj)
         
         tf = false;
         
         try
            normal = obj.computeNormal;
            
            % Taken from David Sturzengger code
            if sqrt(normal(1)^2+normal(2)^2) < Constants.tol_norm_vec
               tf = true;
            end
         catch %#ok<*CTCH>
         end
         
      end % isHorizontal
      
      function normal = computeNormal(obj)
         
         vert_mat = obj.vertices2Matrix;
         
         v1 = vert_mat(:,2)-vert_mat(:,1);
         v2 = vert_mat(:,3)-vert_mat(:,1);
         
         normal = cross(v1,v2);
         norm_n = norm(normal);
         
         if norm_n == 0
            return;
         else
            normal = normal/norm_n;
         end
      end % computeNormal
      
      function projectionZ = computeProjectionZ(obj)
         
         vert_mat = obj.vertices2Matrix;
         projectionZ = max(vert_mat(3,:)) - min(vert_mat(3,:));
         
      end % computeProjectionZ
      
      function area = computeArea(obj)
         
         vert_mat = obj.vertices2Matrix;
         
         % Taken from David Sturzengger code
         % make one vertice as origin
         [~,n_vertices] = size(vert_mat);
         v = vert_mat - repmat(vert_mat(:,1),1,n_vertices);
         
         % rotate such that z - component vanishes
         normal =  obj.computeNormal; % this will be the z' coordinate
         x_prime_norm = v(:,2)/norm(v(:,2));
         z_prime_norm = normal;
         y_prime_norm = cross(z_prime_norm,x_prime_norm); % the result should be a right-handed orthogonal coordinate system which is why y=cross(z,x)
         
         T_prime = [x_prime_norm,y_prime_norm,z_prime_norm];
         v_prime = T_prime\v;
         v_prime_2D = v_prime(1:2,:);
         
         area = polyarea(v_prime_2D(1,:)',v_prime_2D(2,:)');
         
         if isnan(area)
            error('BuildingElement:computeArea','Unable to compute area of %s.\n',lower(Constants.buildingelement_name_str));
         end
         
      end % computeArea
      
      function center_vec = computeCenter(obj)
         
         center_vec = mean(obj.vertices2Matrix,2);
      end % computeCenter
   end % methods
   
       methods (Access = {?Building}) % IF_WITH_METACLASS_SUPPORT
   %methods % IF_NO_METACLASS_SUPPORT
      
      function center_of_max_rectangle_vec = computeCenterOfMaxRectangleInHorizontalPolygon(obj)
         
         persistent p_warn
         
         % Taken from David Sturzengger code
         if obj.isHorizontal
            v = obj.vertices2Matrix;
            
            if isempty(which('polybool'))
               if isempty(p_warn)
                  fprintfDbg(1,'Could not find the polybool function, will plot labels of building elements and zones at the mean of their vertices.. \n ');
                  p_warn = true;
               end
               center_of_max_rectangle_vec = mean(v,2);
               return;
            end
            
            n_vertices = size(v,2);
            
            tot_area = obj.computeArea;
            
            max_area = 0;
            center_of_max_rectangle_vec =  nan(3,1);
            
            % z-coordinate
            center_of_max_rectangle_vec(3,1) = v(3,1);
            
            % This part works well if all angles are n*90?, also for
            % non-convex polygons
            C = nchoosek(1:n_vertices,3);
            for i=1:size(C,1) % go through all possible triangles of the polygon
               
               c = C(i,:);
               if v(1,c(1)) == v(1,c(2)) || v(1,c(1)) == v(1,c(3)) || v(1,c(2)) == v(1,c(3)) && ...
                     v(2,c(1)) == v(2,c(2)) || v(2,c(1)) == v(2,c(3)) || v(2,c(2)) == v(2,c(3))
                  
                  area = (max(v(1,c))-min(v(1,c)))*(max(v(2,c))-min(v(2,c))); %#ok<PROP>
                  
                  x = [min(v(1,c));max(v(1,c));max(v(1,c));min(v(1,c))];
                  y = [min(v(2,c));min(v(2,c));max(v(2,c));max(v(2,c))];
                  
                  warning off %#ok<WNOFF>
                  [uni_x, uni_y] = polybool('union',v(1,:),v(2,:),x,y);
                  warning on %#ok<WNON>
                  
                  sum_nan = sum(isnan(uni_x) | isnan(uni_y));
                  
                  if sum_nan>0
                     if any(isnan(uni_x) ~= isnan(uni_y))
                        error('badnan');
                     end
                     ind = [0,find(isnan(uni_x)),length(uni_x)];
                     union_area = 0;
                     for j=1:length(ind)-1
                        union_area = union_area + polyarea(uni_x(ind(j)+1:ind(j+1)-1),uni_y(ind(j)+1:ind(j+1)-1));
                     end
                  else
                     union_area = polyarea(uni_x,uni_y);
                  end
                  
                  if area > max_area && ~(tot_area < 0.99*union_area) %#ok<PROP> % allow for some numerical errors
                     center_of_max_rectangle_vec(1,1) = mean(x);
                     center_of_max_rectangle_vec(2,1) = mean(y);
                     max_area = area; %#ok<PROP>
                  end
               end
            end
            
            % "Backup" solution for polygons with other than n*90? angles
            if any(isnan(center_of_max_rectangle_vec(1:2)))
               center_of_max_rectangle_vec(1:2) = mean(v(1:2,:),2);
            end
               
            
         else
            error('BuildingElment:computeCenterOfMaxRectangleInHorizontalPolygon','Element NOT horizontal.\n');
         end
         
      end % computeCenterOfMaxRectangleInPolygon
   end % methods (Access = {?Building})
end % classdef
