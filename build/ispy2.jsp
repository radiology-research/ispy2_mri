<%@ page import = "java.sql.*" %>
<%@ page import = "edu.ucsf.mrsc.jsp.*" %>
<%@ page import="java.util.*" %>
<%@ include file= "errormsg.jsp" %>
<jsp:useBean id="conn" class ="connect.JdbcConnect" scope="session"/>

<% 
String error_msg = request.getParameter("e"); 

if ( error_msg == null ) {
  error_msg = "";
}
%>

<%!
    public String formSelect(String var, String html) {
        if ( var == null )  {
            var = "";
        } else if ( var.equals("")) {
            var = "";
        } else if ( var.toLowerCase().equals(html.toLowerCase()) )  {
            var = "SELECTED";
        } else {
           var = "";
        }
        return var;
    }

   public String radioCheck(String var, String html) {
      if ( var == null )  {
        var = "";
      } else {
          if ( var.toLowerCase().equals(html.toLowerCase()) )  {
         var = "CHECKED";
       } else {
         var = "";
       }
      }
   return var;
   }

   public String formCheck(String var) {

       if ( var != null )  {
         if ( var.equals("Y") ) {
           var = "CHECKED";
         } else {
           var = "";
         }
       } else {
       var = "";
     }
   return var;
   }
%>

<%
  conn.checkConnection(response,request,session);
  Connection   connection = conn.getConnection();

if (connection == null) {
	return;
}

	String id = request.getParameter("id");
	String action = request.getParameter("action");

	String ispy2_id           		   = "";
	String visit_number			  	   = "";
	String submitted				   = "";
	String mri_date   				   = "";
	String mri_code   	 			   = "";
	String report_returned_date   	   = "";
	String report_returned_code   	   = "";
	String breast					   = "";
	String dce_compliant			   = "";
	String deviation_other_reason 	   = "";
	String deviation_late_exam_overdue = "";
	String volume_calculation  	 	   = "";
	String site					 	   = "";   	
	String tumor_volume_submitted	   = "";
	String auto_timing1_min		  	   = "";
	String auto_timing1_sec		  	   = "";
	String auto_timing1_option		   = "";
	String auto_timing2_min		       = "";
	String auto_timing2_sec		       = "";
	String auto_timing2_option		   = "";
	String scan_duration			   = "";
	String pe_threshold			       = "";
	String bg_grey_threshold		   = "";
	String injection_rate			   = "";
	String flush_volume			       = "";
	String special_handling 		   = "";
	String aegis_issues			       = "";
	String final_processing_location   = "";
	String final_processing_aegis	   = "";
	String comments				       = "";	
	String screen_fail				   = "";	
	String fov1				 		   = "";	
	String fov2				 		   = "";	
	String moco				 		   = "";	
	String motion_brtool			   = "";
	String report_received_date   	   = "";
	String report_received_code   	   = "";
%>
<%

CallableStatement cstmt = connection.prepareCall("{call select_ispy2_sites()}");
ResultSet sites_rs = cstmt.executeQuery();

cstmt = connection.prepareCall("{call select_ispy2_deviation(?)}");

if (id == null) {
	cstmt.setNull(1, java.sql.Types.NUMERIC);
} else {
  cstmt.setInt(1,Integer.parseInt(id));
}

ResultSet deviation_rs = cstmt.executeQuery();

if (id != null) {
	
  	cstmt = connection.prepareCall("{call select_ispy2(?)}");

    if (id.equals("")) {
    	cstmt.setNull(1, java.sql.Types.NUMERIC);
    } else {
      cstmt.setInt(1,Integer.parseInt(id));
    }

  	ResultSet ispy2_rs = cstmt.executeQuery();

		while (ispy2_rs.next()) {
		
		ispy2_id           		    = ispy2_rs.getString("ispy2_id");	
		submitted				    = ispy2_rs.getString("submitted");
		mri_date   				    = ispy2_rs.getString("mri_date");
		mri_code   	 			    = ispy2_rs.getString("mri_code");
		report_returned_date   	    = ispy2_rs.getString("report_returned_date");
		report_returned_code   	    = ispy2_rs.getString("report_returned_code");
		breast					    = ispy2_rs.getString("breast");
		dce_compliant			    = ispy2_rs.getString("dce_compliant");
		deviation_other_reason 	    = ispy2_rs.getString("deviation_other_reason");		
		volume_calculation  	    = ispy2_rs.getString("volume_calculation");		
		tumor_volume_submitted	    = ispy2_rs.getString("tumor_volume_submitted");
		auto_timing1_min		    = ispy2_rs.getString("auto_timing1_min");
		auto_timing1_sec		    = ispy2_rs.getString("auto_timing1_sec");
		auto_timing1_option		    = ispy2_rs.getString("auto_timing1_option");
		auto_timing2_min		    = ispy2_rs.getString("auto_timing2_min");
		auto_timing2_sec		    = ispy2_rs.getString("auto_timing2_sec");
		auto_timing2_option		    = ispy2_rs.getString("auto_timing2_option");
		special_handling 		    = ispy2_rs.getString("special_handling");
		aegis_issues			    = ispy2_rs.getString("aegis_issues");
		final_processing_location   = ispy2_rs.getString("final_processing_location");
		final_processing_aegis	    = ispy2_rs.getString("final_processing_aegis");
		comments				    = ispy2_rs.getString("comments");
		screen_fail				    = ispy2_rs.getString("screen_fail");
		
		//set empty string for null integers
		visit_number			    = ispy2_rs.getString("visit_number");
				
		deviation_late_exam_overdue = String.valueOf(ispy2_rs.getInt("deviation_late_exam_overdue"));
		if (ispy2_rs.wasNull()) { deviation_late_exam_overdue = ""; }
		
		site					    = String.valueOf(ispy2_rs.getInt("site"));
		if (ispy2_rs.wasNull()) { volume_calculation = ""; }
		
		scan_duration			    = String.valueOf(ispy2_rs.getDouble("scan_duration"));
		if (ispy2_rs.wasNull()) { scan_duration = ""; }
		
		pe_threshold			    = String.valueOf(ispy2_rs.getInt("pe_threshold"));
		if (ispy2_rs.wasNull()) { pe_threshold = ""; }

		bg_grey_threshold           = ispy2_rs.getString("bg_grey_threshold");
		injection_rate              = ispy2_rs.getString("injection_rate");
		flush_volume                = ispy2_rs.getString("flush_volume");
		fov1				    	= ispy2_rs.getString("fov1");
		fov2				    	= ispy2_rs.getString("fov2");
		moco				    	= ispy2_rs.getString("moco");
		motion_brtool				= ispy2_rs.getString("motion_brtool");
		report_received_date   	    = ispy2_rs.getString("report_received_date");
		report_received_code   	    = ispy2_rs.getString("report_received_code");
	}
}

DateTime mri_date_dt = new DateTime();
mri_date_dt.formatDateString(mri_date,mri_code);

DateTime report_returned_date_dt = new DateTime();
report_returned_date_dt.formatDateString(report_returned_date,report_returned_code);

DateTime report_received_date_dt = new DateTime();
report_received_date_dt.formatDateString(report_received_date,report_received_code);

%>

<HTML>
<HEAD>
<title>BDB | New Patient</title>
<link rel="STYLESHEET" type="text/css" href="../basic.css">
<script language="JavaScript" type="text/javascript" src="../JS/function.js"></script>
</HEAD>

<BODY BGCOLOR="#FFFFFF" marginwidth="0" marginheight="0" leftmargin="0" rightmargin="0" topmargin="0">
<script language="JavaScript" type="text/javascript" src="../JS/create_html.js"></script>
<script language="JavaScript" type="text/javascript" src="../JS/jxt.js"><!--
function showStatus(msg) {
                window.status = msg
                return true
        }
// -->
</script>

<TABLE bgcolor=#FFFFFF width="810" border="0" cellspacing="0" cellpadding="0" valign="middle">

					<!-- ############### start of header ################# -->

<jsp:include page="../HEADER.jsp">
        <jsp:param name="page_name" value="<%= request.getRequestURI() %>" />
</jsp:include>

					<!-- ############### end of header ################# -->
<TR>
	<td colspan=4>
		<table cellspacing=0 cellpadding=0 width=100% border=0>
		<tr>
		
			<td valign=top>
				<!-- ##### side column table ##### -->
				<table cellspacing=0 cellpadding=0 width=180 border=0>

						<!-- ##### start of notes menu ##### -->

<jsp:include page="../NOTES.jsp">
        <jsp:param name="page_name" value="<%= request.getRequestURI() %>" />
</jsp:include>

						<!-- ##### end of misc menu ##### -->

				</table>
				<!-- ##### end side column table ##### -->
			</td>
			
			<td bgcolor=#000000 rowspan=5><img src="../images/spacer.gif" height=1 width=1 border=0></td>
			
			<td width=628 align=center valign=top>
				<!-- ##### main body table ##### -->
				<table cellspacing=0 cellpadding=0 width=100%>
				<tr><td><img src="../images/spacer.gif" height=40 width=1></td></tr>

<%  if (!error_msg.equals("")) {  %>
<jsp:include page="../ALERT.jsp">
	<jsp:param name="page_name" value="<%= request.getRequestURI() %>" />
        <jsp:param name="alert_msg" value="<%= error_msg %>" />
</jsp:include>
<%  }  %>	
				<tr>
					<td align=center valign=top>
						<table cellspacing=0 cellpadding=0 width=510>
						<tr>		
							<td><span class="pageHeader">Insert ISPY2 Protocol Deviation</span></td>
						</tr>
						<tr>
							<td background="../images/dot2.gif"><img src="../images/spacer.gif" height=3 width=1></td>
						</tr>
						<tr>
							<td align=center>
								<FORM name="ispy2" method=post action="ispy2_action.jsp" onsubmit="return submit_page(this)">
								<table cellspacing=1 cellpadding=4 width=100%>

			  <tr>
			    <td class="fieldName">Protocol Deviation submitted?</td>
			    <td class="fieldElement">
			      <table cellpadding=3 width=100%>
			        <td class="fieldElement" colspan=3>
			  		<select name="submitted">
			          	<option value="" >
			            	<option value="Y" <%= formSelect(submitted, "Y") %>>Yes
			  			<option value="N" <%= formSelect(submitted, "N") %>>No
			  		</select>
			        </td>
			      </tr>
			      </table>
			  </tr>
					
                <tr>
                  <td class="fieldName">ISPY-2 ID</td>
                  <td class="fieldElement">
                    <table cellpadding=3 width=100%>
                      <td class="fieldElement" colspan=3>
						<input type="text" name="ispy2_id" size="5" maxlength="5" value="<%= ispy2_id == null ? "" : ispy2_id %>">
						<select name="visit_number">
                        	<option value="" >
                          	<option value="1" <%= formSelect(visit_number, "1") %>>1
							<option value="2" <%= formSelect(visit_number, "2") %>>2
							<option value="2.5" <%= formSelect(visit_number, "2.5") %>>2.5
							<option value="3" <%= formSelect(visit_number, "3") %>>3
							<option value="3.5" <%= formSelect(visit_number, "3.5") %>>3.5
							<option value="4" <%= formSelect(visit_number, "4") %>>4
							<option value="5" <%= formSelect(visit_number, "5") %>>5
						</select>
                      </td>
                    </tr>
                    </table>
                </tr>

                <tr>
                  <td class="fieldName">MRI Date</td>
                  <td class="fieldElement">
                    <table cellpadding=3 width=100%>
                    <tr>
                      <td class="fieldElement" colspan=3>
                        <select name="mri_month"><%= mri_date_dt.printHtmlMonthTag() %></select> <b>/</b>
                        <select name="mri_day"><%= mri_date_dt.printHtmlDayTag() %></select> <b>/</b>
                        <input type="text" name="mri_year" size=5 maxlength=4 value="<%= mri_date_dt.getYear() %>">
                      </td>
                    </tr>
                    </table>
                </tr>

			  <tr>
			    <td class="fieldName">Breast</td>
			    <td class="fieldElement">
			      <table cellpadding=3 width=100%>
			        <td class="fieldElement" colspan=3>
			  		<select name="breast">
			          	<option value="" >
			            <option value="r" <%= formSelect(breast, "r") %>>Right
			  			<option value="l" <%= formSelect(breast, "l") %>>Left
			  		</select>
			        </td>
			      </tr>
			      </table>
			  </tr>


            <tr>
              <td class="fieldName">DCE Protocol compliant</td>
              <td class="fieldElement">
			      <table cellpadding=3 width=100%>
			        <td class="fieldElement" colspan=3>
			  		<select name="dce_compliant">
			          	<option value="" >
			            <option value="Y" <%= formSelect(dce_compliant, "Y") %>>Yes
			  			<option value="N" <%= formSelect(dce_compliant, "N") %>>No
			  		</select>
			        </td>
			      </tr>
			      </table>
            </tr>
            <tr>
              <td class="fieldName">Screen fail</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="checkbox" name="screen_fail" value="Y" <%= formCheck(screen_fail) %>>&nbsp;
                  </td>
                </tr>
                </table>
            </tr>			
				<tr>
					<td class="fieldName">If not compliant, what was deviation?<br><span class="fieldNote">(check all that apply)</span></td>
					<td class="fieldElement">
						<table cellpadding=2 width=100%>
							
					   <%  while (deviation_rs.next()) {  %>
						  <tr>
						  	<td class="fieldElement">
						  	  <input type="checkbox" name="deviation[]" value="<%= deviation_rs.getString("id") %>" <%= deviation_rs.getString("has_reason") != null ? "CHECKED" : "" %>>&nbsp;<%= deviation_rs.getString("deviation") %>
						  	  
						  	  <% if (deviation_rs.getInt("id") == 6) { %>
						  	  	&nbsp;-&nbspDays overdue<input type="text" name="deviation_late_exam_overdue" size="2" maxlength="3" value="<%= deviation_late_exam_overdue == null ? "" : deviation_late_exam_overdue %>">&nbsp;days
						  	  <% } %>
						  	  
						  	  <% if (deviation_rs.getInt("id") == 12) { %>
						  	  	<tr>
		                  	  	  <td class="fieldElement">
		                  	  	    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<i>If other, please state reason:</i>
		                  	  	  </td>
		                  	  	</tr>
		                  	  	<tr>
		                  	  	  <td class="fieldElement">
		                  	  	    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<textarea name="deviation_other_reason" rows=2 cols=50 WRAP><%= deviation_other_reason == null ? "" : deviation_other_reason %></textarea>
		                  	  	  </td>
		                  	  	</tr>
		                  	  <% } %>   	
						  	</td>
						  </tr>
					   <% } %>
				</table>
				</td>
			</tr>

            <tr>
              <td class="fieldName">Volume Calculation</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                    <select name="volume_calculation">
                    	<option value="" >
                      	<option value="Possible" <%= formSelect(volume_calculation, "Possible") %>>Possible
						<option value="Not Possible" <%= formSelect(volume_calculation, "Not Possible") %>>Not Possible
                    </select>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Site</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                    <select name="site">
                    	<option value="" >
						<%  while (sites_rs.next()) {  %>
							 <option value="<%= sites_rs.getString("site") %>" <%= formSelect(sites_rs.getString("site"), site) %>><%= sites_rs.getString("site") %> <%= sites_rs.getString("name") %>
						<%  } %>
                    </select>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Tumor Volume Submitted</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="text" name="tumor_volume_submitted" size=6 maxlength=6 value="<%= tumor_volume_submitted == null ? "" : tumor_volume_submitted %>">
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Auto Timing</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                  <td class="fieldElement" colspan=3>
					<input type="text" name="auto_timing1_min" size="3" maxlength="4" value="<%= auto_timing1_min == null ? "" : auto_timing1_min %>">&nbsp;:&nbsp;<input type="text" name="auto_timing1_sec" size="3" maxlength="4" value="<%= auto_timing1_sec == null ? "" : auto_timing1_sec %>">
					<select name="auto_timing1_option">
                    	<option value="">
                      	<option value="1" <%= formSelect(auto_timing1_option, "1") %>>1
						<option value="2" <%= formSelect(auto_timing1_option, "2") %>>2
						<option value="3" <%= formSelect(auto_timing1_option, "3") %>>3
						<option value="4" <%= formSelect(auto_timing1_option, "4") %>>4
					</select>
					&nbsp;/&nbsp;
					<input type="text" name="auto_timing2_min" size="3" maxlength="4" value="<%= auto_timing2_min == null ? "" : auto_timing2_min %>">&nbsp;:&nbsp;<input type="text" name="auto_timing2_sec" size="3" maxlength="4" value="<%= auto_timing2_sec == null ? "" : auto_timing2_sec %>">
					<select name="auto_timing2_option">
                    	<option value="">
                      	<option value="5" <%= formSelect(auto_timing2_option, "5") %>>5
						<option value="6" <%= formSelect(auto_timing2_option, "6") %>>6
						<option value="7" <%= formSelect(auto_timing2_option, "7") %>>7
						<option value="8" <%= formSelect(auto_timing2_option, "8") %>>8
					</select>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Scan Duration </td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="text" name="scan_duration" size="5" maxlength="5" value="<%= scan_duration == null ? "" : scan_duration %>">&nbsp;<i>temporal resolution in seconds (80-100s)</i>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">PE Threshold Processed</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="text" name="pe_threshold" size="5" maxlength="2" value="<%= pe_threshold == null ? "" : pe_threshold %>">&nbsp;%
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Background/Grey Threshold</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                     <input type="text" name="bg_grey_threshold" size="5" maxlength="2" value="<%= bg_grey_threshold == null ? "" : bg_grey_threshold %>">&nbsp;%
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Injection rate <br>2cc/second</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
			<input type="checkbox" name="injection_rate" value="Y" <%= formCheck(injection_rate) %>>&nbsp;
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Flush volume <br>20 cc</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
			<input type="checkbox" name="flush_volume" value="Y" <%= formCheck(flush_volume) %>>&nbsp;
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Special Handling necessary (header reading, other)</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="checkbox" name="special_handling" value="Y" <%= formCheck(special_handling) %>>&nbsp; <i>See comments</i>
                  </td>
                </tr>
                </table>
            </tr>
            <tr>
              <td class="fieldName">Problems loading on AEGIS</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="checkbox" name="aegis_issues" value="Y" <%= formCheck(aegis_issues) %>>&nbsp; <i>See comments</i>
                  </td>
                </tr>
                </table>
            </tr>
            <tr>
              <td class="fieldName">Final (official) processing done by UCSF?</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                    <select name="final_processing_location">
                    	<option value="" >
                      	<option value="UCSF" <%= formSelect(final_processing_location, "UCSF") %>>UCSF
						<option value="Site" <%= formSelect(final_processing_location, "Site") %>>Site
                    </select>
					&nbsp;
                    <select name="final_processing_aegis">
                    	<option value="" >
                      	<option value="AEGIS" <%= formSelect(final_processing_aegis, "AEGIS") %>>AEGIS
						<option value="No AEGIS" <%= formSelect(final_processing_aegis, "No AEGIS") %>>No AEGIS
                    </select>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Comments</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
					 <textarea name="comments" rows=4 cols=60 WRAP><%= comments == null ? "" : comments %></textarea>
                  </td>
                </tr>
                </table>
            </tr>
			
            <tr>
              <td class="fieldName">FOV</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                     <input type="text" name="fov1" size="5" maxlength="2" value="<%= fov1 == null ? "" : fov1 %>">&nbsp; x&nbsp;
					 <input type="text" name="fov2" size="5" maxlength="2" value="<%= fov2 == null ? "" : fov2 %>">
                  </td>
                </tr>
                </table>
            </tr>
					
            <tr>
              <td class="fieldName">MOCO to pre in Aegis</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="checkbox" name="moco" value="Y" <%= formCheck(moco) %>>
                  </td>
                </tr>
                </table>
            </tr>

            <tr>
              <td class="fieldName">Motion- brtool registration</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
				  	<input type="checkbox" name="motion_brtool" value="Y" <%= formCheck(motion_brtool) %>>
                  </td>
                </tr>
                </table>
            </tr>
						
            <tr>
              <td class="fieldName">Report received date</td>
              <td class="fieldElement">
                <table cellpadding=3 width=100%>
                <tr>
                  <td class="fieldElement" colspan=3>
                    <select name="report_received_month"><%= report_received_date_dt.printHtmlMonthTag() %></select> <b>/</b>
                    <select name="report_received_day"><%= report_received_date_dt.printHtmlDayTag() %></select> <b>/</b>
                    <input type="text" name="report_received_year" size=5 maxlength=4 value="<%= report_received_date_dt.getYear() %>">
                  </td>
                </tr>
                </table>
            </tr>
			
                <tr>
                  <td class="fieldName">Report returned to site</td>
                  <td class="fieldElement">
                    <table cellpadding=3 width=100%>
                    <tr>
                      <td class="fieldElement" colspan=3>
                        <select name="report_returned_month"><%= report_returned_date_dt.printHtmlMonthTag() %></select> <b>/</b>
                        <select name="report_returned_day"><%= report_returned_date_dt.printHtmlDayTag() %></select> <b>/</b>
                        <input type="text" name="report_returned_year" size=5 maxlength=4 value="<%= report_returned_date_dt.getYear() %>">
                      </td>
                    </tr>
                    </table>
                </tr>


								</table>
							</td>
						</tr>
						<tr>
							<td background="../images/dot2.gif"><img src="../images/spacer.gif" height=3 width=1></td>
						</tr>
						<tr>
							<td align=center>
								<table cellspacing=0 cellpadding=15>
								<tr>
									<td><input type="submit" name="submit" value="Submit" class="formButton"></td>
									<td><input type="reset" name="reset" class="formButton"></td>
									<input type="hidden" name="id" value="<%= id %>" />
									<input type="hidden" name="action" value="<%= action %>" />
								</tr>
								</table>
								</FORM>
						</tr>
						</table>
					</td>
				</tr>
				<tr><td><img src="../images/spacer.gif" height=60 width=1></td></tr>
				</table>
				<!-- ##### end main body table ##### -->
			</td>
			
		</tr>
		</table>
	</td>
	<td bgcolor=#000000><img src="../images/spacer.gif" height=1 width=1 border=0></td>
</TR>

					<!-- ############### start of footer ################# -->

<jsp:include page="../FOOTER.jsp">
        <jsp:param name="page_name" value="<%= request.getRequestURI() %>" />
</jsp:include>

					<!-- ############### end of footer ################# -->

</TABLE>
</BODY>
</HTML>
