require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

$| = 1;

my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$WHICHDB    = $in{'WHICHDB'};

($WHICHDB)  = &StripJunk($WHICHDB);

&readsetCookies;

$PH_ID = 0;
print qq#Set-Cookie:PH_ID=$PH_ID;           path=/; domain=$cookie_server;\n#;
print qq#Set-Cookie:AreteUser=''            path=/; domain=$cookie_server;\n#;

if ( $USER ) {
   &MyAreteRxHeader;
   &AreteRxHeaderBlock;
} else {
#   &ReconRxGotoNewLogin;

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

&read_this_Owners_Pharmacies($USER, $TYPE);
&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
   print qq#<!-- displayWebPage -->\n#;
 
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );
   my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($TS);
   $year += 1900;
   $date = qq#$abbr[$mon] $mday, $year#; 
   $DATE    = sprintf("%02d/%02d/%04d", $mon+1, $mday, $year);
   $SFDATE  = sprintf("%04d-%02d-%02d", $year, $mon+1, $mday);
   $SFDATE2 = sprintf("%04d%02d%02d",   $year, $mon+1, $mday);
 
   ($PROG = $prog) =~ s/_/ /g;

   &process_notifications;

   print qq#<h2>Pharmacy Selection</h2>\n#;
   print qq#<p>Please select the pharmacy you wish to view from the list below:</p>\n#;
    
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
   print "<tr><th>$nbsp</th><th>Pharmacy Name</th><th>NCPDP</th><th>NPI</th><th>Phone</th><th>Address</th><th>ID</th></tr>\n";
   print "</thead>\n";
   print "<tbody>\n";

   foreach $Pharmacy_ID (sort { $Pharmacy_Names{$a} cmp $Pharmacy_Names{$b} } keys %Pharmacies) {
      print "<tr>";
      print qq#<td>#;
      $URLH = "MyReconRx.cgi";
      print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
      print qq#<INPUT TYPE="hidden" NAME="PH_ID" VALUE="$Pharmacy_ID">\n#;
      print qq#<INPUT TYPE="Submit" NAME="Submit" VALUE="Select">\n#;
      print qq#</FORM>\n#;
      print qq#</td>#;
      print "<td width=150>$Pharmacy_Names{$Pharmacy_ID}</td>\n";
      print "<td>$Pharmacy_NCPDPs{$Pharmacy_ID}</td>\n";
      print "<td>$Pharmacy_NPIs{$Pharmacy_ID}</td>\n";
      print "<td>$Pharmacy_Business_Phones{$Pharmacy_ID}</td>\n";
      print "<td>$Pharmacy_Addresses{$Pharmacy_ID}<br>$Pharmacy_Citys{$Pharmacy_ID}, $Pharmacy_States{$Pharmacy_ID} $Pharmacy_Zips{$Pharmacy_ID}</td>\n";
      print "<td>$Pharmacy_ID</td>\n";
      print "</tr>\n";
      print qq#<!--end pharmacy to select-->\n#;
   }

   print "</tbody>";
   print "</table>\n";
}

#______________________________________________________________________________

sub process_notifications {

   my ($ENV) = &What_Env_am_I_in;
   print "ENV: $ENV<br>\n" if ($debug);

   @dirnames = ( "Emergency", "Page_1_Notifications" );

   foreach $dirname (@dirnames) {
      if ( $ENV =~ /DEV/i ) {
         $dskpath = "\\\\webdev\\WWW\\www.recon-rx.com\\Webshare\\$dirname";
      } else {
         $dskpath = "\\\\$WBSERVER\\WWW\\www.recon-rx.com\\Webshare\\$dirname";
      }

      my @infiles;
   
      if ( -d "$dskpath" ) {
         opendir(DIR, "$dskpath") or warn "can't open dir: $dskpath:<br>$!<br>";
         while (defined($file = readdir(DIR))) {
             $fullfilename = "$dskpath/$file";
             if ( -d "$fullfilename" || $file =~ /^\./ || $file =~ /.swp$|~$/i || $file =~ /YYYY/i ) {
                print qq#Skip file: $file<br>\n# if ($debug);
             } else {
                if ( $file !~ /Filename format/i ) {
                   print qq#do something with "$dskpath\\$file"<br>\n# if ($debug);
                   push(@infiles, "$dskpath\\$file");
                }
             }
         }
         closedir(DIR);
      }
    
      foreach $filename (sort @infiles) {
         if ( -e "$filename" ) {
		   if ($fullfilename =~ /emergency/i) {
             print qq#<div class="notification emergency">\n#;
		   } else {
		     print qq#<div class="notification">\n#;
		   }
           my $cnt = 0;
           open (FILE, "< $filename") || warn "Couldn't open file Emergency.txt.<br>\n$!<br>\n";
           while (<FILE>) {
              chomp;
              my $line = $_;
              $line = $nbsp if ( $line =~ /^\s*$/ );
              $cnt++;
              if ( $cnt == 1 ) {
                 if ( $dirname =~ /Emergency/i ) {
                    $title = "Emergency Notification";
                 } elsif ( $dirname =~ /Page_1/i ) {
                    $title = "Notification";
                 }
                 print qq#<H2>$title:</H2>\n#;
                 print qq#<P>\n#;
              }
              print qq#$line<br>\n#;
           }
           print qq#</P>\n# if ($cnt >= 1);
           print qq#</div>\n#;
           close(FILE);
         }
      }
   }
}

#______________________________________________________________________________
 
