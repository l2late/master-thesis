

function writeCellToFile(c,filename,writeToCSV)
   %WRITECELLTOFILE If possible (see xlswrite documentation) writes a cellarray of strings to an xls-file otherwise to an ';' delimited csv-file.   
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
   
   
   if nargin<3
      writeToCSV = false;
   end
   
   [p,fn] = fileparts(filename); % remove extension
   filename = [p,filesep,fn];
   
   try
      
      if writeToCSV
         error('ERR');
      end
      fn_xls = strcat(filename,Constants.fileextension_XLS);
      
      if exist(fn_xls,'file')
         delete(fn_xls);
      end
      [status, message] = xlswrite(fn_xls,c);
      if status ~= 1 || ~isempty(message.message)
         if exist(fn_xls,'file')
            delete(fn_xls);
         end
         error('ERR');
      end
      
   catch  %#ok<CTCH>
      
      if ~writeToCSV
         fprintfDbg(1,'Writing to .xls was not successful, writing to ";" separated .csv instead. \n');
      end
      
      % write instead into a .csv file
      fid = fopen(strcat(filename,Constants.fileextension_CSV),'w');
      c_num = cellfun(@numericToString,c,'uniformoutput',0);
      c_new = regexprep(c_num,';','');
      
      if ~isequalwithequalnans(c_num,c_new)
         fprintfDbg(1,'Replaced all '';'' with '''' when writing to .csv. \n');
      end
      for i=1:size(c_new,1)
         fprintf(fid,'%s;',c_new{i,:});
         fprintf(fid,'\n');
      end
      fclose(fid);
      
   end

end

function out = numericToString(in)
   
   if isnumeric(in)
      out = num2str(in,Constants.num2str_precision);
   else
      out = in;
   end
   
end
      
   
