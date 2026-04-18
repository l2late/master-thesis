classdef EHFModelBaseClass
   %EHFMODELBASECLASS 	This class builds the base class of the external heat flux models of a building.
   % See the documentation for a detailed description of this class
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
   
   
   properties(Constant)
      
      identifiers_fullModel_str@char = 'identifiers_fullModel';
      
   end
   properties(Constant,Abstract)
      
      multiIncludeOk@logical;
      
   end
   
   properties(SetAccess = protected)
      EHF_identifier@char;              % EHF identifier for the specific model
      Aq@double;                        % state x to state q matrix
      Bq_u@double;                      % Input u to state q matrix
      Bq_v@double;                      % Input v to state q matrix
      Bq_vu@double;                     % cube matrix for the bilinear part of the model
      Bq_xu@double;                     % cube matrix for the bilinear part of the model
      identifiers@Identifier;           % Model specific identifiers for states, inputs, disturbances and constraints
      source_file@char = '';            % source file path of the EHF data
      
   end
   
   properties
      class_file@char = '';         % class file name of the derived model class
   end
   
   % Abstract method makes the entire class abstract. It is not possible
   % to instantiate an abstract class. Subclasses of an abstract class are
   % will become concrete (instantiable) if they implement all properties
   % and methods that are defined as abstract.
   % See Matlab help:
   % >> web('/Applications/MATLAB_R2013a.app/help/matlab/matlab_oop/abstract-classes-and-interfaces.html', '-helpbrowser')
   
   methods(Abstract)
      
      [Fx,Fu,Fv,g,constraint_identifiers] = getConstraintsMatrices(obj,parameters)
      
      [Cu] = getCostVector(parameters)
      
   end % methods(Abstract)
   
   methods
      
      function [A,Bu,Bv,Bxu,Bvu] = getPrescribedSizeSystemMatrices(obj,identifiers)
         
         % check: identifiers of appropriate type
         if ~isa(identifiers,Constants.identifier_classname_str)
            error('getPrescribedSizeSystemMatrices:Argument','Argument 1 of type %s required.\n',Constants.identifier_classname_str);
         end
         
         n_x_prescribed = length(identifiers.x);
         n_q_prescribed = length(identifiers.q);
         n_u_prescribed = length(identifiers.u);
         n_v_prescribed = length(identifiers.v);
         
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         A = obj.Aq;
         Bu = zeros(n_q_prescribed,n_u_prescribed);
         Bv = zeros(n_q_prescribed,n_v_prescribed);
         Bxu = zeros(n_q_prescribed,n_x_prescribed,n_u_prescribed);
         Bvu = zeros(n_q_prescribed,n_v_prescribed,n_u_prescribed);
         
         % Bu, Bxu, Bvu
         for i = 1:n_u
            idx_u_prescribed = getIdIndex(identifiers.u,obj.identifiers.u{i});
            Bu(:,idx_u_prescribed) = obj.Bq_u(:,i);
            Bxu(:,:,idx_u_prescribed) = obj.Bq_xu(:,:,i);
            
            for j = 1:n_v
               idx_v_prescribed = getIdIndex(identifiers.v,obj.identifiers.v{j});
               Bvu(:,idx_v_prescribed,idx_u_prescribed) = obj.Bq_vu(:,j,i);
            end
         end
         
         for j = 1:n_v
            idx_v_prescribed = getIdIndex(identifiers.v,obj.identifiers.v{j});
            Bv(:,idx_v_prescribed) = obj.Bq_v(:,j);
         end
        
      end
      
      function checkNan(obj)
         
         if isempty(obj.Aq)
            fprintfDbg(2,'In %s: checking for NaNs, but the matrices appear not to be set.\n\n',obj.EHF_identifier);
            return;
         end
         
         m = {'Aq','Bq_u','Bq_v','Bq_vu','Bq_xu'};
         for i=1:length(m)
            if anyyy(isnan(obj.(m{i})))
               error('checkNan:isNaN','In %s: %s matrix contains NaNs.\n\n',obj.EHF_identifier,m{i});
            end
         end
         
         fprintfDbg(2,'In %s: No NaNs detected in the matrices.\n\n',obj.EHF_identifier);
         
      end
      
      function [Fx,Fu,Fv,g,constraint_identifiers] = getPrescribedSizeConstraintsMatrices(obj,identifiers,parameters)
                  
         % get dimensions
         n_u_prescribed = length(identifiers.u);
         n_v_prescribed = length(identifiers.v);
         
         n_u = length(obj.identifiers.u);
         n_v = length(obj.identifiers.v);
         
         % size of model specific constraints
         n_c = length(obj.identifiers.constraints);
         
         Fu = zeros(n_c,n_u_prescribed);
         Fv = zeros(n_c,n_v_prescribed);
         
         % Fx, g  and constraint_identifiers do not change
         [Fx,Fu_i,Fv_i,g,constraint_identifiers] = obj.getConstraintsMatrices(parameters);
         
         for j = 1:n_u
            idx_u_prescribed = getIdIndex(identifiers.u,obj.identifiers.u{j});
            Fu(:,idx_u_prescribed) = Fu_i(:,j);
         end
         
         for j = 1:n_v
            idx_v_prescribed = getIdIndex(identifiers.v,obj.identifiers.v{j});
            Fv(:,idx_v_prescribed) = Fv_i(:,j);
         end
      end % getPrescribedSizeConstraintsMatrices
      
      function [cu] = getPrescribedSizeCostVector(obj,identifiers,parameters)
         
         % get dimensions
         n_u_prescribed = length(identifiers.u);
         n_u = length(obj.identifiers.u);
         
         cu = zeros(n_u_prescribed,1);
         
         cu_i = obj.getCostVector(parameters);
         for j = 1:n_u
            idx_u_prescribed = getIdIndex(identifiers.u,obj.identifiers.u{j});
            cu(idx_u_prescribed) = cu_i(j);
         end         
         
      end % getPrescribedSizeCostVector
      
   end % methods
end % classdef
