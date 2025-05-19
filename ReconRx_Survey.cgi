
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$tdate  = sprintf("%04d%02d%02d", $year, $month, $day);
$DATEEX = sprintf("%02d/%02d/%04d", $month, $day, $year);
#______________________________________________________________________________

&readPharmacies(0, $PROGRAM, $inNCPDP);

if ( $USER ) {  
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

print << "EOL";
<link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css" />

<script>


</script>

EOL

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);


  if ( $in{'Submit'} =~ /Save Changes/i ) {
    &update_questions();
    &remove_action();
    print qq#<h1 style="color: \#3584a6">Thank You for updating your information!</h1>\n#;
    exit;
  }




$ntitle = "ReconRx Program Feedback";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

#print qq#<h2>Please update your contact information. Note: Payment Confirmation Contact and Claim Research Contact Information Required</h2>\n#;

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  
  print qq#<!-- displayWebPage -->\n#;
  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return checkRequiredFields(this)\;">\n#;
  print qq#<INPUT TYPE="hidden" NAME="submitter" ID="submitter" "VALUE="">\n#;

   print qq#<p><div class="q1div"; id="q1div"; style="background-color: LightBlue" display: block'>
       <h1>1. If I need assistance, my ReconRx Account Manager will help me.</h1> 
           <table class='noborders' ><tr>
	   <td><input type="radio" id="rmaassist" name="rmaassist" value="5" required="required"><label>Strongly Agree</label></td>
	   <td><input type="radio" id="rmaassist" name="rmaassist" value="4" required="required"><label>Agree</label></td>
	   <td><input type="radio" id="rmaassist" name="rmaassist" value="3" required="required"><label>Neutral</label></td>
	   <td><input type="radio" id="rmaassist" name="rmaassist" value="2" required="required"><label>Disagree</label></td>
	   <td><input type="radio" id="rmaassist" name="rmaassist" value="1" required="required"><label>Strongly Disagree</label></td>	         
           </table></tr>
   </div></p>#;
   print qq#<br>#;
   
   print qq#<div class="q2div" id="q2div" style='background: LightBlue; display: block'>
       <h1>2. The ReconRx website is easy to navigate.</h1> 
           <table class='noborders' ><tr>
	   <td> <input type="radio" id="easynav" name="easynav" value="5" required="required"><label>Strongly Agree</label></td>
	   <td> <input type="radio" id="easynav" name="easynav" value="4" required="required"><label>Agree</label></td>
	   <td> <input type="radio" id="easynav" name="easynav" value="3" required="required"><label>Neutral</label></td>
	   <td> <input type="radio" id="easynav" name="easynav" value="2" required="required"><label>Disagree</label></td>
	   <td> <input type="radio" id="easynav" name="easynav" value="1" required="required"><label>Strongly Disagree</label></td>
           </table></tr>
   </div>#;
   print qq#<br>#;
   
   print qq#<p><div class="q3div" id="q3div" style='background: LightBlue; display: block'>
       <h1>3. I find the reports available in ReconRx to be useful.</h1> 
           <table class='noborders' ><tr>
	   <td> <input type="radio" id="rptuse" name="rptuse" value="5" required="required"><label>Strongly Agree</label></td>
	   <td> <input type="radio" id="rptuse" name="rptuse" value="4" required="required"><label>Agree</label></td>
	   <td> <input type="radio" id="rptuse" name="rptuse" value="3" required="required"><label>Neutral</label></td>
	   <td> <input type="radio" id="rptuse" name="rptuse" value="2" required="required"><label>Disagree</label></td>
	   <td> <input type="radio" id="rptuse" name="rptuse" value="1" required="required"><label>Strongly Disagree</label></td>
           </table></tr>
   </div>#;
   print qq#<br>#;
   
   print qq#<p><div class="q4div" id="q4div" style='background: LightBlue; display: block'>
       <h1>4. Overall, the ReconRx program meets my reconciliation needs.</h1> 
           <table class='noborders' ><tr>
	   <td> <input type="radio" id="overall" name="overall" value="5" required="required"><label>Strongly Agree</label></td>
	   <td> <input type="radio" id="overall" name="overall" value="4" required="required"><label>Agree</label></td>
	   <td> <input type="radio" id="overall" name="overall" value="3" required="required"><label>Neutral</label></td>
	   <td> <input type="radio" id="overall" name="overall" value="2" required="required"><label>Disagree</label></td>
	   <td> <input type="radio" id="overall" name="overall" value="1" required="required"><label>Strongly Disagree</label></td>
           </table></tr>
	         
   </div></p>#;
   
   print qq#<p><div class="q6div" id="q6div" style='display: block'>
       <h1>Additional Comments</h1> 
	   <textarea id="addcom" name="addcom" rows="5" cols="100" maxlength="500"></textarea>
	  	         
   </div></p>#;   
   
   print qq#<div id="errors"></div>\n#;

   print qq#<INPUT id="submit" style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Save Changes">\n#;
   print "</FORM>";
}

#______________________________________________________________________________

sub remove_action {
  $sql = "DELETE FROM officedb.pharmacy_action_req
           WHERE Pharmacy_ID = $PH_ID
             AND action = 'Survey'";

#  print "$sql<br><br>";

  $rows = $dbx->do("$sql") or warn $DBI::errstr;
}

#______________________________________________________________________________


sub update_questions {
	$q1a = $in{'rmaassist'};
	$q2a = $in{'easynav'};
	$q3a = $in{'rptuse'};
	$q4a = $in{'overall'};
	$addcomm = $in{'addcom'};
        $addcomm =~ s/\'/\\'/g;
##  $PH_ID = '11' if($USER =! /^(66|69)$/);
	
	#print "PH_ID: $PH_ID  q1a: $q1a  q2a: $q2a q3a: $q3a  q4a: $q4a addcomm: $addcomm\n";
	
	$sql = "REPLACE INTO testing.questionnaire
	       VALUES ($PH_ID, $q1a, $q2a, $q3a, $q4a, '$addcomm', CURRENT_DATE())";
				
    $rows = $dbx->do("$sql") or warn $DBI::errstr;
}
