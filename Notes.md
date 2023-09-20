This holds some notes by Ross Boylan <ross.boylan@ucsf.edu> about the operation of the bdb web app, which we are trying to replicate.  The format is markdown, meaning it should be intelligible as plain text but will look better if viewed with a markdown formatter.  I use the one in Visual Studio Code.

Deviation Reasons
=================
`ispy2.jsp` has the code to insert a record of receiving an exam (set of scans) and the QA process.  It presents a longish list of reasons the exam might have deviated from the protocol; the user selects one or more of them (checkboxes) and then submits the results.

`deviation_rs` gets the resuls of `call select_ispy2_deviation(?)` where the argument is either an id, an integer, or `NULL`.  It's not obvious to me how it could be anything but `NULL` at the start, but I don't really know what sequence things execute in.  But if it's `NULL` the only difference is that every value in `has_reason` is `NULL`--it still lists all the reasons, in order of position.  The lowest numbered resulting `id` is 1, not 0.

Based on direct examination of that procedure in the database, it does
```sql
      SELECT dr.id AS 'id', dr.deviation AS 'deviation', d.ispy2_deviation_reason_id AS 'has_reason'
      FROM 
         dbo.ispy2_deviation_reason  AS dr 
            LEFT OUTER JOIN dbo.ispy2_deviation  AS d 
            ON dr.id = d.ispy2_deviation_reason_id AND d.ispy2_tbl_id = @ispy2_id
      ORDER BY dr.position ASC
```

Here are the columns in `ispy2_deviation_reason`:

|COLUMN_NAME|DATA_TYPE|TYPE_NAME|PRECISION|LENGTH|SCALE|RADIX|NULLABLE|REMARKS|COLUMN_DEF|SQL_DATA_TYPE|SQL_DATETIME_SUB|CHAR_OCTET_LENGTH|ORDINAL_POSITION|IS_NULLABLE|SS_DATA_TYPE
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|id|2|numeric() identity|5|7|0|10|0|NULL|NULL|2|NULL|NULL|1|NO|63
|deviation|12|varchar|100|100|NULL|NULL|0|NULL|NULL|12|NULL|100|2|NO|39
|archive|1|char|1|1|NULL|NULL|1|NULL|NULL|1|NULL|1|3|YES|39
|position|4|int|10|4|0|10|1|NULL|NULL|4|NULL|NULL|4|YES|38

and `ispy2_deviation` where the main deviation data is kept:
|COLUMN_NAME|DATA_TYPE|TYPE_NAME|PRECISION|LENGTH|SCALE|RADIX|NULLABLE|REMARKS|COLUMN_DEF|SQL_DATA_TYPE|SQL_DATETIME_SUB|CHAR_OCTET_LENGTH|ORDINAL_POSITION|IS_NULLABLE|SS_DATA_TYPE|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|id|2|numeric() identity|5|7|0|10|0|NULL|NULL|2|NULL|NULL|1|NO|63
|ispy2_tbl_id|2|numeric|5|7|0|10|0|NULL|NULL|2|NULL|NULL|2|NO|63
|ispy2_deviation_reason_id|4|int|10|4|0|10|0|NULL|NULL|4|NULL|NULL|3|NO|56

The result set is then used to populate


```jsp
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
```
Apparently `name="deviation[]"` indicates that an array named `deviation` is being constructed; the value are `id`'s from `ispy2_deviation_reason` which are not in any simple order.

`ispy2_action.jsp` takes over once the form is submitted.  It does
`String deviation[] = request.getParameterValues("deviation[]");` and, after inserting the main info,

```jsp
// Insert/update ispy2_deviation table
cstmt = connection.prepareCall("{call insert_ispy2_deviation(?,?)}");

//Literal string for sp exec
String deviation_reason = "NULL";

if (deviation != null) {
  if (deviation.length > 0) {
     deviation_reason = deviation[0];
  
    for (int i=1; i<deviation.length; i++) {
  	  deviation_reason += ",";
      deviation_reason += deviation[i];
    }	
  }
}
cstmt.setInt(1, ispy2_tbl_id);
cstmt.setString(2, deviation_reason);
cstmt.execute();
cstmt.close(); 
```

Here is the stored procedure (from the db):
```sql
ALTER PROCEDURE [dbo].[insert_ispy2_deviation]  
   @ispy2_tbl_id numeric(5, 0) = NULL,
   @deviation_string varchar(500) = 'null'
AS 
   /*Generated by SQL Server Migration Assistant for Sybase version 7.4.0.*/
   BEGIN

      DECLARE
         @delimiter char(1)

      DECLARE
         @pattern varchar(500)

      DECLARE
         @pos int

      DECLARE
         @piece varchar(500)

      DECLARE
         @sql varchar(500)

      SET @delimiter = ','

      SET @sql = 'DELETE from ispy2_deviation WHERE ispy2_deviation_reason_id NOT IN (' + @deviation_string + ') AND ispy2_tbl_id = ' + CONVERT(varchar(10), @ispy2_tbl_id)

      /*
      *   SSMA warning messages:
      *   S2SS0028: Dynamic SQL statements cannot be automatically converted.
      */

      EXECUTE (@sql)

      IF (@deviation_string != 'null')
         BEGIN

            /* Need to tack a delimiter onto the end of the input string if one doesn't exist*/
            IF right(nullif(rtrim(@deviation_string), ''), 1) <> @delimiter
               SET @deviation_string = @deviation_string + @delimiter

            SET @pattern = '%' + @delimiter + '%'

            SET @pos = patindex(@pattern, @deviation_string)

            WHILE @pos <> 0
            
               BEGIN

                  SET @piece = left(@deviation_string, @pos - 1)

                  IF NOT EXISTS 
                     (
                        SELECT dbo.ispy2_deviation.id AS id
                        FROM dbo.ispy2_deviation
                        WHERE dbo.ispy2_deviation.ispy2_tbl_id = @ispy2_tbl_id AND dbo.ispy2_deviation.ispy2_deviation_reason_id = CONVERT(int, @piece)
                     )
                     INSERT dbo.ispy2_deviation(ispy2_tbl_id, ispy2_deviation_reason_id)
                        VALUES (@ispy2_tbl_id, CONVERT(int, @piece))

                  SET @deviation_string = stuff(@deviation_string, 1, @pos, '')

                  SET @pos = patindex(@pattern, @deviation_string)

               END

         END

   END
```
So the comma-separated string constructed in the jsp is used literally in a `DELETE` and then pulled apart and each value is inserted into the `ispy2_deviation` table, unless it is already there.

Testing
=======
The program won't do anything useful without a lot of setup (see the Prerequisites in the installation instruction), and it's a GUI.  So automatic testing is not feasible, even though `hatch` set up a testing infrastructure.  That said, there are a lot of things to test:
  * `py pre_fields.py` should generate `ispy2_gui.py` in a different directory.  At least as an academic point, your current working directory should not affect `pre_fields.py` if you leave it in place.
  * Appropriately uploaded to the public project web site.
  * Appropriately uploaded to PyPI.
  * Installable following the instructions.
  * Runs
    * by typing program name in a terminal
    * by clicking on a shortcut if set up
    * by running ispy2_gui.py directly, in place (e.g., `C:\Users\rdboylan\AppData\Roaming\Python\Python310\site-packages\ispy2_mri\ispy2_gui.py` for me right now)
  * Inserts data into database.  Verify that with an independent program.
  * Note that the deviations are kept in a separate table in the database, so check that they are recorded and properly associated with the main record.
  * The program is likely not robust against exceptional situations:
    * Invalid dates, like 2/31/2023
    * Text input file has visit or institution that doesn't line up exactly with existing choices.
    * Text input file not formatted as expected.
    * Small screen.
    * Duplicate entry of the same information.
    * It will let you enter a received date that is after the returned date.