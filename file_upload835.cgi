#!/usr/bin/perl

use CGI;
use File::Basename;
use File::Copy qw' copy ';

require "D:/RedeemRx/cgi-bin/cgi-lib.pl";
require "D:/RedeemRx/MyData/Common_routines.pl";

my %in;
my $date;
my $www = 'members';
$www = 'www' if ($ENV{'SERVER_NAME'} =~ /^dev./);
my ($sec,$min, $hour, $day, $month, $year) = (localtime)[0,1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$date  = sprintf("%04d%02d%02d%02d%02d%02d", $year, $month, $day, $hour, $min, $sec);

&readsetCookies;

my $q = CGI->new;
print $q->header;
my $upload_dir = "D:\\WWW\\${www}.recon-rx.com\\WebShare\\uploads\\835Upload\\";
my @files = $q->param("multi_files");
my @io_handles=$q->upload('multi_files');
my %file_hash;
$cnt = @files;

if ( !$cnt ) {
   print "<script>parent.callback('There was a problem uploading your file (try a smaller file).')</script>";
   exit;
}


foreach my $file(@files){
    if ( $file !~ /.txt$|.dat$|.zip$|.tar$/i ) {
      print "<script>parent.callback('File Upload Failed Due to Incorrect File Type')</script>";
      exit;
    }

    foreach my $sub_item(@io_handles){
        if($file eq $sub_item){
            $file_hash{$file} = $sub_item;
        }
    }
}

my $remit_type  = $q->url_param('remit_type');
$upload_dir .= $remit_type;

chdir $upload_dir or die "Cannot chdir to upload destination directory: $!\n";

foreach my $key(keys %file_hash){
	my $base = basename($file_hash{$key});    
        my $tmpfilename = $q->tmpFileName($file_hash{$key});
        my $destFile = File::Spec->catfile($upload_dir,$base);
	$destFile =~ s/$file_hash{$key}/${PH_ID}_${date}_$file_hash{$key}/;
	copy($tmpfilename, "${destFile}") or die "Copy to ($upload_dir) failed: $!\n";

}
    print "<script>parent.callback('File Upload:-->Success!')</script>";

exit;


