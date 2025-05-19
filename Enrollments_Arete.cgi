require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1;

my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

$status = $in{'status'};

if ( $USER ) {
   &MyAreteRxHeader;
   &AreteRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

&readPharmacies;

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
   my $complete_checked = '';
   my $archived_checked = '';

   print qq#<script>
              \$(document).ready(function() {
                 \$('input[name=status]').change(function(){
                    \$('form[name=radio_form]').submit();
                 });
              });
            </script>#;

   print qq#<!-- displayWebPage -->\n#;
 
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
 
   ($PROG = $prog) =~ s/_/ /g;

   if ($status =~ /complete/i) {
     $complete_checked = 'checked';
   } else {
     $archived_checked = 'checked';
   }

   print qq#<h2>Completed Enrollments</h2>\n#;
   print qq#<p>All completed enrollments in the system, waiting to be put into PAI Desktop.</p>\n#;
   
   print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
   print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
   print qq#<script type="text/javascript" charset="utf-8"> \n#;
   print qq#\$(document).ready(function() { \n#;
   print qq#                \$('\#tablef').dataTable( { \n#;
   print qq#                                "sScrollX": "100%", \n#;
   print qq#                                "bScrollCollapse": true,  \n#;
   print qq#                                "sScrollY": "370px", \n#;
   print qq#                                "bPaginate": false \n#;
   print qq#                } ); \n#;
   print qq#} ); \n#;
   print qq#</script> \n#;

   print qq#<table id="tablef">\n#;
   print "<thead>\n";
   print "<tr><th>Completed</th><th>Status</th><th>Pharmacy</th><th>NCPDP</th><th>Details</th></tr>\n";
   print "</thead>\n";
   print "<tbody>\n";

   $status = "'pending','pending_coo'";

   my $numrowsc = 0;
   my $sql = "";

   $sql = "SELECT rrx_status, rrx_enrollment_start, rrx_pharmname, rrx_ncpdp, rrx_npi, COO, id, rrx_psao
             FROM reconrxdb.enrollment 
            WHERE (rrx_status IN ($status)) 
              &&  rrx_PSAO = 'Arete'
         ORDER BY rrx_enrollment_start DESC";

   ($sqlout = $sql) =~ s/\n/<br>\n/g;

   $sthrp = $dbx->prepare($sql);
   $sthrp->execute();
   my $numofrows = $sthrp->rows;

   while ( my ( $status, $enrollment_start, $Pharmacy_Name, $NCPDP, $NPI, $coo, $id, $psao ) = $sthrp->fetchrow_array()) {
     print "<tr>";
     $coo_display = '';
     $coo_display = '(COO)' if($coo > 0);

     if ( $psao =~ /Arete/ ) {
       $style = "background: #5FC8ED; color: #FFFFFF;";
     }
     else {
       $style = "";
     }

     print qq#<td>$enrollment_start</td>#;
     print qq#<td>$status</td>#;
     print qq#<td>${Pharmacy_Name}$coo_display</td>#;
     print qq#<td>$NCPDP</td>#;
     print qq#<td><form action="../Arete_enroll_review.php" method="post">
                    <INPUT class="button-form-xsmall" style="$style" TYPE="submit" VALUE="View Details">
                    <input type="hidden" name="admin_ncpdp" value="$NCPDP">
                    <input type="hidden" name="admin_npi" value="$NPI">
                    <input type="hidden" name="admin_id" value="$id">
                  </form>
		</td>#;
     print qq#</tr>\n#;
   }

   $sthrp->finish;
 
   print qq#</tbody>\n#;
   print qq#<tr>#;
   print qq#</table>\n#;

   print qq#<div style="clear: both;"></div>#;
   print qq#<br>\n#;
}

#______________________________________________________________________________

