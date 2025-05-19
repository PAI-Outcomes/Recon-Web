#______________________________________________________________________________
#
# Jay Herder
# Date: 06/13/2012
# TPP_Checklist.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
  $incdebug++;
  $debug++;
  $verbose++;
}
#####$dbitrace++;
#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$debug   = $in{'debug'}   if (!$debug);
$verbose = $in{'verbose'} if (!$verbose);

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$CUSTOMERID = $in{'CUSTOMERID'};
$LTYPE      = $in{'LTYPE'};
$LDATEADDED = $in{'LDATEADDED'};
$TS         = $in{'TS'};
$CHK        = $in{'CHK'};
$OWNER      = $in{'OWNER'};
$OWNERPASS  = $in{'OWNERPASS'};

($USER) = &StripJunk($USER);
($PASS) = &StripJunk($PASS);
($TS)   = &StripJunk($TS);
($CHK)  = &StripJunk($CHK);

$debug++ if ( $verbose );
$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";
$CUSTOMERID = "" if ( !$CUSTOMERID );

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
   $inNCPDP   = $USER;
   $dispNCPDP = $USER;
} else {
   $inNCPDP   = $in{'inNCPDP'};
   $dispNCPDP = $in{'dispNCPDP'};
}
if ( $PASS ) {
   $inNPI   = $PASS;
   $dispNPI = $PASS;
} else {
   $inNPI   = $in{'inNPI'};
   $dispNPI = $in{'dispNPI'};
}

#______________________________________________________________________________

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);
#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);

# print qq#USER: $USER, PASS: $PASS, VALID: $VALID, isMember: $isMember\n# if ($debug);

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;
   &ReconRxGotoNewLogin;

   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
#______________________________________________________________________________

&readPharmacies;

#______________________________________________________________________________

print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
   print "dol0: $0<br>\n";
   print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
   print "<hr size=4 noshade color=blue>\n";
   print "PROG: $PROG<br>\n";
   print "<br>\n";
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
   my $key;
   foreach $key (sort keys %in) {
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
#  print "inNPI: $inNPI, dispNPI: $dispNPI<br>\n";
#  print "inNCPDP: $inNCPDP, dispNCPDP: $dispNCPDP<br>\n";
   print "<hr size=4 noshade color=blue>\n";
}

&displayWebPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

   print qq#<!-- displayWebPage -->\n#;
   print "sub displayWebPage: Entry.<br>\n" if ($debug);

   $FMT = "%0.02f";
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
#  print "date: $date, DATE: $DATE, SFDATE: $SFDATE, SFDATE2: $SFDATE2<br>\n" if ($debug);
   # date: Jun 13, 2012, DATE: 06/13/2012

   ($PROG = $prog) =~ s/_/ /g;
   print qq#<h2><i>Third Party Payer Check List: $date - Check \# $CHK</i></h2>\n#;

#####

   print qq#<a href="javascript:history.go(-1)">Return</a><br>\n#;

   my $TOTAL_Amount_Billed  = 0;
   my $TOTAL_Amount_CoPayed = 0;
   my $TOTAL_Amount_Payed   = 0;
   my $TOTAL_Trans_Fee      = 0;
   my $TOTAL_Claim_Adjustment_Transaction = 0;
   my $TOTAL_Adjustment_Amount = 0;

   my $dbin     = "R8DBNAME";
   my $DBNAME   = $DBNAMES{"$dbin"};
   my $TABLE    = $DBTABN{"$dbin"};
   my $FIELDS   = $DBFLDS{"$dbin"};
   my $FIELDS2  = $DBFLDS{"$dbin"} . "2";
   my $fieldcnt = $#${FIELDS2} + 2;
 
   $dbz = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
          { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   DBI->trace(1) if ($dbitrace);

# RX NUM,  FILL DATE,  AMOUNT BILLED, AMOUNT COPAY, AMOUNT PAID, TRANS FEE

   my $sql = "SELECT $$FIELDS FROM $DBNAME.$TABLE WHERE R_TRN02_Check_Number='$CHK' AND R_BPR16_Date LIKE '%$SFDATE2%' ORDER BY R_CLP01_Rx_Number";

   print "sql:<br>$sql<br>\n" if ($verbose);
 
   $stb = $dbz->prepare($sql);
   $numofrows = $stb->execute;
   print "numofrows: $numofrows<br>\n" if ($debug);

   if ( $numofrows <= 0 ) {
     print "No records found for this Check Number<br>\n";
   } else {

     print qq#<table border=5 cellspacing=0 cellpadding=0>\n#;
     &print_Heading_Line;

     my $ptr = 0;
     while (my @row = $stb->fetchrow_array()) {
       (@$FIELDS3) = @row;
       $jptr = -1;
       foreach $pc (@$FIELDS3) {
         $jptr++;
         my $name = @$FIELDS2[$jptr];
   #     print "$name: $pc<br>\n" if ($verbose);
         ${$name} = "$pc";
       }
       

       $Amount_Billed        = "\$" . &commify(sprintf("$FMT", $R_CLP03_Amount_Billed));
       $Amount_CoPayed       = "\$" . &commify(sprintf("$FMT", $R_CLP05_Amount_CoPayed));
       $Amount_Payed         = "\$" . &commify(sprintf("$FMT", $R_CLP04_Amount_Payed));

       $Trans_Fee03_01       = "\$" . &commify(sprintf("$FMT", $R_CAS03_01_Trans_Fee));
       $Trans_Fee03_02       = "\$" . &commify(sprintf("$FMT", $R_CAS03_02_Trans_Fee));
       $Trans_Fee03_03       = "\$" . &commify(sprintf("$FMT", $R_CAS03_03_Trans_Fee));
       $Trans_Fee03_04       = "\$" . &commify(sprintf("$FMT", $R_CAS03_04_Trans_Fee));
       $Trans_Fee06_01       = "\$" . &commify(sprintf("$FMT", $R_CAS06_01_Trans_Fee));
       $Trans_Fee06_02       = "\$" . &commify(sprintf("$FMT", $R_CAS06_02_Trans_Fee));
       $Trans_Fee06_03       = "\$" . &commify(sprintf("$FMT", $R_CAS06_03_Trans_Fee));
       $Trans_Fee06_04       = "\$" . &commify(sprintf("$FMT", $R_CAS06_04_Trans_Fee));
       $Trans_Fee09_01       = "\$" . &commify(sprintf("$FMT", $R_CAS09_01_Trans_Fee));
       $Trans_Fee09_02       = "\$" . &commify(sprintf("$FMT", $R_CAS09_02_Trans_Fee));
       $Trans_Fee09_03       = "\$" . &commify(sprintf("$FMT", $R_CAS09_03_Trans_Fee));
       $Trans_Fee09_04       = "\$" . &commify(sprintf("$FMT", $R_CAS09_04_Trans_Fee));
       $Trans_Fee12_01       = "\$" . &commify(sprintf("$FMT", $R_CAS12_01_Trans_Fee));
       $Trans_Fee12_02       = "\$" . &commify(sprintf("$FMT", $R_CAS12_02_Trans_Fee));
       $Trans_Fee12_03       = "\$" . &commify(sprintf("$FMT", $R_CAS12_03_Trans_Fee));
       $Trans_Fee12_04       = "\$" . &commify(sprintf("$FMT", $R_CAS12_04_Trans_Fee));
       $Trans_Fee15_01       = "\$" . &commify(sprintf("$FMT", $R_CAS15_01_Trans_Fee));
       $Trans_Fee15_02       = "\$" . &commify(sprintf("$FMT", $R_CAS15_02_Trans_Fee));
       $Trans_Fee15_03       = "\$" . &commify(sprintf("$FMT", $R_CAS15_03_Trans_Fee));
       $Trans_Fee15_04       = "\$" . &commify(sprintf("$FMT", $R_CAS15_04_Trans_Fee));
       $Trans_Fee18_01       = "\$" . &commify(sprintf("$FMT", $R_CAS18_01_Trans_Fee));
       $Trans_Fee18_02       = "\$" . &commify(sprintf("$FMT", $R_CAS18_02_Trans_Fee));
       $Trans_Fee18_03       = "\$" . &commify(sprintf("$FMT", $R_CAS18_03_Trans_Fee));
       $Trans_Fee18_04       = "\$" . &commify(sprintf("$FMT", $R_CAS18_04_Trans_Fee));

       $Claim_Adj_Trans03_01 = "\$" . &commify(sprintf("$FMT", $R_CAS03_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans03_02 = "\$" . &commify(sprintf("$FMT", $R_CAS03_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans03_03 = "\$" . &commify(sprintf("$FMT", $R_CAS03_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans03_04 = "\$" . &commify(sprintf("$FMT", $R_CAS03_04_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans06_01 = "\$" . &commify(sprintf("$FMT", $R_CAS06_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans06_02 = "\$" . &commify(sprintf("$FMT", $R_CAS06_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans06_03 = "\$" . &commify(sprintf("$FMT", $R_CAS06_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans06_04 = "\$" . &commify(sprintf("$FMT", $R_CAS06_04_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans09_01 = "\$" . &commify(sprintf("$FMT", $R_CAS09_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans09_02 = "\$" . &commify(sprintf("$FMT", $R_CAS09_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans09_03 = "\$" . &commify(sprintf("$FMT", $R_CAS09_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans09_04 = "\$" . &commify(sprintf("$FMT", $R_CAS09_04_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans12_01 = "\$" . &commify(sprintf("$FMT", $R_CAS12_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans12_02 = "\$" . &commify(sprintf("$FMT", $R_CAS12_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans12_03 = "\$" . &commify(sprintf("$FMT", $R_CAS12_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans12_04 = "\$" . &commify(sprintf("$FMT", $R_CAS12_04_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans15_01 = "\$" . &commify(sprintf("$FMT", $R_CAS15_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans15_02 = "\$" . &commify(sprintf("$FMT", $R_CAS15_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans15_03 = "\$" . &commify(sprintf("$FMT", $R_CAS15_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans15_04 = "\$" . &commify(sprintf("$FMT", $R_CAS15_04_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans18_01 = "\$" . &commify(sprintf("$FMT", $R_CAS18_01_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans18_02 = "\$" . &commify(sprintf("$FMT", $R_CAS18_02_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans18_03 = "\$" . &commify(sprintf("$FMT", $R_CAS18_03_Claim_Adjustment_Transaction));
       $Claim_Adj_Trans18_04 = "\$" . &commify(sprintf("$FMT", $R_CAS18_04_Claim_Adjustment_Transaction));

       print qq#<tr> <td>$R_CLP01_Rx_Number</td> <td>$R_DTM02_Date</td> <td align=right>$Amount_Billed</td> <td align=right>$Amount_CoPayed</td> <td align=right>$Amount_Payed</td> \n#;

       print qq#<td nowrap>#;
       my ($stuff) = &jprintit_plus_ADD("Claim_Adjustment_Reason_Code");
       print qq#</td>\n#;

       print qq#<td nowrap>#;
       my ($TTF) = &jprintit_plus_ADD("Trans_Fee");
       $TOTAL_Trans_Fee += $TTF;
       print qq#</td>\n#;

       print qq#<td nowrap>#;
       my ($TCAT) = &jprintit_plus_ADD("Claim_Adjustment_Transaction");
       $TOTAL_Claim_Adjustment_Transaction += $TCAT;
       print qq#</td>\n#;

       print qq#<td align=left>$R_CLP02_Claim_Status_Meaning</td>
                <td>$R_DTM01_Date_Time_Qualifier_Meaning</td>
                </tr>\n#;
#
#               <td>$R_TPP</td>
#               <td>$R_BPR02_Check_Amount</td></td>

       $TOTAL_Amount_Billed  += $R_CLP03_Amount_Billed;
       $TOTAL_Amount_CoPayed += $R_CLP05_Amount_CoPayed;
       $TOTAL_Amount_Payed   += $R_CLP04_Amount_Payed;
#
#      $TOTAL_Trans_Fee      += $R_CAS03_Trans_Fee;
#      $TOTAL_Claim_Adjustment_Transaction += $R_CAS03_Claim_Adjustment_Transaction;
#
       $TOTAL_Adjustment_Amount += $R_PLB04_Adjustment_Amount;

       $ptr++;
       if ( $ptr == 10 ) {
          $ptr = 0;
          &print_Heading_Line;
       }
     }
     $OTOTAL_Amount_Billed  = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_Billed));
     $OTOTAL_Amount_CoPayed = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_CoPayed));
     $OTOTAL_Amount_Payed   = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_Payed));
     $OTOTAL_Trans_Fee      = "\$" . &commify(sprintf("$FMT", $TOTAL_Trans_Fee));
     $OTOTAL_Claim_Adj_Trans= "\$" . &commify(sprintf("$FMT", $TOTAL_Claim_Adjustment_Transaction));
     $OTOTAL_Adj_Amount     = "\$" . &commify(sprintf("$FMT", $TOTAL_Adjustment_Amount));
     $Check_Amount         = "\$" . &commify(sprintf("$FMT", $R_BPR02_Check_Amount)); # same val on each record...

     $TOTAL_Costs  = $TOTAL_Trans_Fee + $TOTAL_Claim_Adjustment_Transaction + $TOTAL_Adjustment_Amount;
     $OTOTAL_Costs = "\$" . &commify(sprintf("$FMT", $TOTAL_Costs));

#    print "<tr><th colspan=10><hr></th></tr>\n";
     print "<tr><th colspan=2>Totals</th>
       <th align=right>$OTOTAL_Amount_Billed</th>
       <th align=right>$OTOTAL_Amount_CoPayed</th>
       <th align=right>$OTOTAL_Amount_Payed</th>
       <th>$nbsp</th>
       <th align=right>$OTOTAL_Trans_Fee</th>
       <th align=right>$OTOTAL_Claim_Adj_Trans</th>
       <th colspan=4>&nbsp;</th></tr>\n";

#    print "ptr: $ptr<br>\n";
     &print_Heading_Line if ( $ptr > 9);
     print qq#<tr><th colspan=10 class="red">$nbsp</th>\n#;

     print qq#<tr><th colspan=4>Total Amount Billed:</th> <th align=right>$OTOTAL_Amount_Billed</th> <th colspan=5>$nbsp</th> </tr>\n#;
     print qq#<tr><th colspan=5>$nbsp Total Transaction Fees:</th> <th align=right>$OTOTAL_Trans_Fee</th> <th colspan=4>$nbsp</th> </tr>\n#;
     print qq#<tr><th colspan=5>$nbsp Total Claim Adjustments:</th> <th align=right>$OTOTAL_Claim_Adj_Trans</th> <th colspan=4>$nbsp</th> </tr>\n#;
     print qq#<tr><th colspan=5>$nbsp Total Adjustment Amount (Service Fee) (PLB04's):</th> <th align=right>$OTOTAL_Adj_Amount</th> <th colspan=4>$nbsp</th> </tr>\n#;

     print qq#<tr><th colspan=5>Total Costs:</th> <th class="red" align=right>$OTOTAL_Costs</th> <th colspan=4>$nbsp</th> </tr>\n#;
     print qq#<tr><th colspan=4>Total Check Amount: (BPR02)</th> <th class="green" align=right>$Check_Amount </th> <th colspan=5>$nbsp</th></tr>\n#;
     print qq#</table>\n#;
   }

   $stb->finish;
   $dbz->disconnect;
#####

   print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

sub print_Heading_Line {

  print qq#<tr>#;
  print qq#<th>Rx Num #;
  print qq#(CLP01)# if ( $debug );
  print qq#</th>#;
  print qq#<th>Fill Date #;
  print qq#(DTM02)# if ( $debug );
  print qq#</th>#;
  print qq#<th>Amount Billed #;
  print qq#(CLP03)# if ( $debug );
  print qq#</th>#;
  print qq#<th>Amount CoPay #;
  print qq#(CLP05)# if ( $debug );
  print qq#</th>#;
  print qq#<th>Amount Paid #;
  print qq#(CLP04)# if ( $debug );
  print qq#</th>#;
  print qq#<th>Claim Adj Reason Code #;
  print qq#(CAS02)# if ( $debug );
  print qq#</th>#; 
  print qq#<th>Trans Fee #;
  print qq#(CAS03)# if ( $debug );
  print qq#</th>#; 
  print qq#<th>Claim Adj #;
  print qq#(CAS03)# if ( $debug );
  print qq#</th>#; 
  print qq#<th>Claim Status Meaning #;
  print qq#(CLP02)# if ( $debug );
  print qq#</th>#; 
  print qq#<th>Date Time Qualifier Meaning #;
  print qq#(DTM01)# if ( $debug );
  print qq#</th>#; 
  print qq#</tr>\n#;

#    <th>Payer</th> 
#    <th>Check Amount</th>

}

#______________________________________________________________________________

sub jprintit_plus_ADD {

   my ($type) = @_;
   my ($i, $j, $vartest, $valtest, $varname, $val);
   my $TOTAL = 0;

   my $linescount = 0;
   for ($i=3; $i<=18; $i+=3) {
       for ($j=1; $j <= 4; $j++) {
           $vartest = sprintf("R_CAS%02d_%02d_Claim_Adjustment_Reason_Code", $i-1, $j);
           $valtest = $$vartest;
#print "i: $i, j: $j, vartest: $vartest, value: $valtest<br>\n";

           $vartest1 = sprintf("R_CAS%02d_%02d_Trans_Fee", $i, $j);
           $vartest2 = sprintf("R_CAS%02d_%02d_Claim_Adjustment_Transaction", $i, $j);
#print "vartest1: $vartest1, vartest2: $vartest2<br>\n";
           $valtest1 = $$vartest1;
           $valtest2 = $$vartest2;
#print qq# if ($valtest1 < $valtest2 ) { <br>\n#;

#print "type: $type<br>\n";
#
           if ( ( $type =~ /^Trans_Fee/i && $valtest1 && ($valtest1 != $valtest2) ) ||
                ( $type !~ /^Trans_Fee/i && $valtest2 && ($valtest2 != $valtest1) )  ) {

             if ( $valtest ) {
                $varname = sprintf("R_CAS%02d_%02d_%s", $i, $j, $type);
                $val = $$varname;
                $TOTAL += $valtest1 + $valtest2;
#               print "varname: $varname<br>val: $val<br>TOTAL: $TOTAL<br>\n" if ( $type !~ /Reason/i );
                $linescount++;
                if ($linescount == 1 ) {
                   print qq#<table border=1 cellspacing=0 cellpadding=0 width=100%>\n#;
                }
                if ( $type =~ /Reason/i ) {
                   $var0 = sprintf("R_CAS01_%02d_Claim_Adjustment_Group_Code", $j);
                   $val0 = $$var0;
                   print qq#<tr><td>$val0</td> <td align=right>$valtest</td></tr>#;
                } else {
                   print qq#<tr><td align=right>$val</td></tr>#;
                }
             }
           }
       }
   }
   print qq#</table>\n# if ($linescount > 0 );
#  print "TOTAL: $TOTAL<br>\n";
   return($TOTAL);
}

#______________________________________________________________________________
